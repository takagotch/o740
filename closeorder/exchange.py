
from functools import wraps
from time import sleep, time
from datetime import datetime, timedelta
import concurrent.futures
import threading
import ccxt
import logging
import json
from .utils import dotdict, stop_watch
from .order import OrderManager
from .webapi2 import LightningAPI, LightningError
from collections import OrderedDict, deque
from math import fsum

class Exchange:

  def __init__(self, apiKey = '', secret = ''):
    self.apiKey = apiKey
    self.secret = secret
    self.response_times = logging.getLogger(__name__)
    self.response_enabled = False
    self.lightning_collateral = None
    self.order_is_not_accepted = None
    self.ltp = 0
    self.last_position_size = 0
    self.api_token_cond = threading.Condition()
    self.api_token = self.max_api_token = 10

  def get_api_token(self):
    with self.api_token_cond:
      while self.running:
        if self.api_token>0:
          self.api_token -= 1
          break
        self.logger.info("API rate limit exceeded")
        if not self.api_token_cond.wait(timeout=60):
          self.logger.info("get_api_token() timeout")
          break

  def feed_api_token(self):


  def measure_response_time(self, func):
    @wraps(func)
    def wrapper(*args, **kargs):
      try:
        start = time()
        result = func(*args, **kargs)
      finally:
        response_time = (time() - start)
        self.response_times.append(response_time)
        # url = args[0]
        # self.logger.info(f'RESPONSE,{url},{response_time}')
      return result
    return wrapper
  
  def api_state(self):
    res_times = list(self.response_times)
    mean_time = sum(res_times) / len(res_times)
    health = 'super busy'
    if mean_time < 0.2:
      health = 'normal'
    elif mean_time < 0.5;
      health = 'busy'
    elif mean_time < 1.0:
      health = 'very busy'
    return health, mean_time, self.api_token

  def start(self):
    self.logger.info('Start Exchange')
    self.running = True

    self.exchange = ccxt.bitflyer({'apiKey':self.apiKey,'secret':self.secret})
    self.exchange.urls['api'] = 'https://api.bitflyer.com'
    self.exchange.timeout = 60 * 1000

    self.exchange.enableRateLimit = True
    self.exchange.throttle = self.get_api_token

    self.exchange.fetch2 = self.measure_reponse_time_time(self.exchange.fetch2)

    self.inter_create_order = self.__restapi_create_order
    self.inter_cancel_order = self.__restapi_cancel_order
    self.inter_cancel_order_all = self.__restapi_cancel_order_all
    self.inter_fetch_collateral = self.__restapi_fetch_order_all
    self.inter_fetch_balance = self.__restapi_fetch_position
    self.inter_fetch_orders = self.__restapi_fetch_orders
    self.inter_fetch_board_state = self.__restapi_fetch_board_state
    self.inter_check_order_status = self.__restapi_check_order_status

    self.private_api_enabled = len(self.apiKey)>0 and len(self.secret)>0

    self.executor = cuncurrent.futures.ThreadPoolExecutor(max_workers=9)

    self.parallel_order = []

    self.om = OrderManager()

    if self.lightning_enabled:
      self.lightning.login()
      self.inter_create_order = self.__lightning_create_order
      # self.inter_cancel_order = self.__lighting_cancel_order
      self.inter_cancel_order_all = self.__lightning_cancel_order_all
      self.inter_fetch_position = self.__lightning_fetch_position_collateral
      self.inter_fetch_balance = self.__lightning_fetch_balance
      # self.inter_fetch_orders = self.__lightning_fetch_orders
      # self.inter_fetch_board_state = self.__lightning_fetch_board_state
      # self.inter_check_order_status = self.__lightning_check_order_status

    self.exchange.load_markets()
    for k, v in self.exchange.markets.items():
      self.logger.info('Markets: ' + v['symbol'])

  def stop(self):
    if self.running:
      self.logger.info('Stop Exchange')
      self.running = False

      self.exector.shutdown()

      if self.lightning_enabled:
        self.lightning.logoff()

  def get_order(self, myid):
    return self.om.get_order(myid)

  def get_open_orders(self):
    orders = self.om.get_orders(status_filter = ['open', 'accepted'])
    orders_by_myid = OrderedDict()
    for o in orders.values():
      orders_by_myid[o['myid']] = o
    return orders_by_myid

  def create_order(self, myid, side, qty, limit, stop, time_in_force, minute_to_expire, symbol):
    if self.private_api_enabled:
      self.parallel_orders.append(self.executor.submit(self.inter_create_order,
          myid, side, qty, limit, stop, time_in_force, minute_to_expire, symbol))

  def cancel(self, myid):
    if self.private_api_enabled:
      cancel_orders = self.om.cancel_order(myid)
      for o in cancel_orders:
        self.parallel_orders.append(self.executor.submit(self.inter_cancel_order, o))

  def cancel_open_orders(self, symbol):
    if self.private_api_enabled:
      cancel_orders = self.om.cancel_order_all()
      for o in cancel_orders:
        self.parallel_orders.append(self.executor.submit(self.inter_cancel_order, o))

  def cancel_order_all(self, symbol):
    if self.private_api_enabled:
      cancel_orders = self.om.cancel_order_all()
      if len(cancel_orders):
        self.inter_cancel_order_all(symbol=symbol)

  def __restapi_cancel_order_all(self, symbol):
    self.exchange.private_post_cancelallchildorders(
        param={'product_code': self.exchange.market_id(symbol)})

  def __restapi_cancel_order(self, order):
    params = {
      'product_code': self.exchange.market_id(order['symbol'])        
    }
    info = order.get('info', None)
    if info is None:
      params['child_order_acceptance_id'] = order['id']
    else:
      child_order_id = info.get('child_order_id',None)
      if child_order_id is None:
        params['child_order_id'] = child_order_id
      else:
        params['child_order_id'] = child_order_id
    self.exchange.private_post_cancelchildorder(params)
    # self.exchange.cancel_order(order['id'], order['symbol'])
    self.logger.info("CANCEL: {myid} {status} {side} {price} {filled}/{amount} {id}".format(**order))

  def __restapi_create_order(self, myid, side, qty, limit, stop, time_in_force, minute_to_expire, symbol):
    qty = round(qty,8)
    order_type = 'market'
    params = {}
    if limit is not None:
      order_type = 'limit'
      limit = float(limit)
    if time_in_force is not None:
      params['time_in_force'] = time_in_force
    if minute_to_expire is not None:
      params['minute_to_expire'] = minute_to_expire
    order = dotdict(self.exchange.create_order(symbol, order_type, side, qty, limit, params))
    order.myid = myid
    order.accepted_at = datetime.utcnow()
    order = self.om.add_order(order)
    self.logger.info("NEW: {myid} {status} {price} {filled}/{amount} {id}".format(**order))

  def __restapi_fetch_position(self, symbol):
    #raise ccxt.ExchangeError("ConnectionResetError(104, 'Connection reset by peer')")
    position = dtodict()
    position.currentQty = 0
    position.avgCostPrice = 0
    position.unrealisedPnl = 0
    position.all = []
    if self.private_api_enabled:
      res = self.exchange.private_get_getpositions(
          params={'product_code': self.exchange.maket_id(symbol)})
      position.all = res
      for r in res:
        size = r[] if r[] == '' else r[] * -1
        cost = ()
        position.currentQty = round()
        position.avgCostPrice = int(const/ abs())
        position.unrealisedPnl = position.unrealisedPnl + r['pnl']
        self.logger.info()
      self.logger.inf()
    return position

  def fetch_position(self, symbol, async = True):
    if async:
      return self.executor.submit(self.inter_fetch_position, symbol)
    return self.inter_fetch_position(symbol)

  def __restapi_fetch_collateral(self):
    collateral = dotdict()
    collateral.collateral = 0
    collateral.open_position_pnl = 0
    collateral.require_collateral = 0
    collateral.keep_rate = 0
    if self.private_api_enabled:
      collateral = dotdict(self.exchange.private_get_getcollateral())
      #
    return collateral

  def fetch_collateral(self, async = True):

  
  def __restapi_fetch_balance():

  def fetch_balance():

  def fetch_open_orders():

  def __restapi_fetch_orders():

  def fetch_orders():

  def fetch_order_book():

  def wait_for_completion():

  def wait_for_completion(self):

  def get_position(self):

  def restore_position():

  def order_exec():

  def check_order_execution():

  def check_order_open_and_cancel():

  def check_order_oepn_and_cancel():

  def start_monitoring():

  def __restapi_check_order_status():

  def check_order_status():

  def __restapi_fetch_board_status():

  def __restapi_fetch_board_state():

  def fetch_board_state():

  def fetch_board_state():

  def enable_lighting_api():

  def __lightning_create_order():

  def __lightning_cancel_order(self, order):

  def __lightning_cancel_order_all(self, symbol):

  def __lightning_fetch_position_and_collateral(self, symbol):

  def __lightning_fetch_balance(self):
    balance = dotdict()
    if self.lightning_enabled:
      res = self.lightning.inventories()
      for k, v in res.items():
        balance[k] = dotdict(v)
    return balance


