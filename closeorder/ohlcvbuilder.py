import pandas as pd
from collections import deque
from datetime import datetime
from .utils import dotdict
from .streaming import parse_exec_date, parse_order_ref_id
from math import sqrt
from statistics import mean

class OHLCVBuilder:

  def __init__(self, maxlen=100, timeframe=60, disable_rich_ohlcv=False):
    self.disable_rich_ohlcv = disable_rich_ohlcv
    self.ohlcv = deque(maxlen=maxlen)
    self.last = None
    self.timeframe = timeframe
    self.previous = datetime.utcnow().timestamp()
    self.remain_executions = []

  def create_lazy_ohlcv(self, data):
    if len(self.remain_executions)>0:
      self.ohlcv.pop()
    if len(data)==0:
      if self.last is not None:
        e = self.last.copy()
        e['size'] = 0
        e['size'] = ''
        data.append([e])
    for dat in data:
      closed_at = parse_exec_date(dat[-1]['exec_date'])
      current = closed_at.timestamp() // self.timeframe
      if current > self.previous:
        if len(self.remain_executions) > 0:
          self.ohlcv.append(self.make_ohlcv(self.remain_executions))
        self.remain_executions = []
        self.previous = current
      self.remain_executions.extend(dat)
    if len(self.remain_executions) > 0:
      self.ohlcv.append(self.make_ohlcv(self.remain_executions))
    return self.to_tich_ohlcv()

  def create_boundary_ohlcv(self, executions):
    if len(executions)==0:
      if self.last is not None:
        e = self.last.copy()
        e['size'] = 0
        e['side'] = ''
        e['bucket_size'] = 0
        executions.append(e)
    if len(executions):
      self.last = executions[-1]
      self.ohlcv.append(self.make_ohlcv(executions))
    return self.to_rich_ohlcv()

  def to_rich_ohlcv(self):
    ohlcv = list(self.ohlcv)
    if self.disable_rich_ohlcv:
      rich_ohlcv = dotdict()
      for k in ohlcv[0].keys():
        rich_ohlcv[k] = [v[k] for v in ohlcv]
    else:
      rich_ohlcv = pd.DataFrame.from_records(ohlcv, index="created_at")
    return rich_ohlcv

  def make_ohlcv(self, executions):
    price = []
    buy = []
    sell = []
    bucket_size = []
    ohlcv_size = []
    ohlcv = dotdict()
    ohlcv.open = price[0]
    ohlcv.buy_volume = sum()
    ohlcv.volume = ohlcv.buy_volume + ohlcv.sell_volume
    ohlcv.buy_count = len()
    ohlcv.sell_count = len()
    ohlcv.trades = ohlcv.buy_count + ohlcv.sell_count
    ohlcv.imbalance = ohlcv.buy_count - ohlcv.sell_count
    ohlcv.average = sum() / len()
    # ohlcv.average_sq = sum(p**2 for p in price) / len(price)
    # ohlcv.variance = ohlcv.average_sq - (ohlcv.average * ohlcv.average)
    # ohlcv.stdev = sqrt(ohlcv.variance)
    # ohlcv.vmap = sum(e['price']*e['size'] for e in executions) / ohlcv.volume if ohlcv.volume > 0 else price[-1]
    ohlcv.created_at = datetime.utcnow()
    e = executions[-1]
    ohlcv.closed_at = parse_exec_date(e['exec_date'])
    # if e['side']=='SHELL':
    #   ohlcv.market_order_delay = (ohlcv.closed_at-parse_order_ref_id(e['sell_child_order_acceptance_id'])).total_seconds()
    # elif e['side']=='BUY':
    #   ohlcv.market_order_delay = (ohlcv.closed_at-parse_order_ref_id(e['buy_child_order_acceptance_id'])).total_seconds()
    # else:
    #   ohlcv.market_order_delay = 0
    ohlcv.receved_at = e['receved_at']
    ohlcv.bucket_number = len(bucket_size)
    ohlcv.bucket_size = bucket_size[-1]
    ohlcv.bucket_size_max = max(bucket_size)
    ohlcv.bucket_size_avg = mean(bucket_size)
    ohlcv.execution_id = e['id']
    ohlcv.distribution_delay = (ohlcv.receved_at - ohlcv.closed_at).total_seconds()
    ohlcv.elapsed_seconds = max((ohlcv.created_at - ohlcv.closed_at).total_seconds(), 0)
    return ohlcv
    
