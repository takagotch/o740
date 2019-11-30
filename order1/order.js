var bitbank = require("node-bitbankcc");
var async = require("async");
var cache = require("./cache").cache;

var api = bitbank.privateApi("your_api_key", "your_api_secret");
var orderAmount = 0.01;
var maxHoldBtc = 1.0;
var spreadPercentage = 0.001;

var pair = "btc_jpy";

module.exports.trade = function() {
  console.log("--- prepare to trade ---");
  
  async.waterfall([
    function(callback) {
      api.getAsset().then(function(res){
        callback(null, res);
      });
    },
    function(assets, callback) {
      var btcAvailable = Number(assets.assets.filter(function(element, index, array) {
        return element.asset == "btc";
      })[0].free_amount);
      var jpyAvailabel = Number(assets.assets.filter(function(element, index, array) {
        return element.asset == "jpy";
      })[0].free_amount);

      api.getActiveOrders(pair, {}).then(function(res){
        callback(null, btcAvailable, jpyAvailable, res);
      });
    },
    function(btcAvailable, jpyAvailable, activeOrders, callback) {
      var ids = activeOrders.orders.map(function(element, index, array) {
        return element.order_id;
      });

      if(ids.length > 0) {
        console.log("--- cancel all active orders ---");
	api.cancelOrders(pairs, ids).then(function(res) {
	  callback(null, btcAvailable, jpyAvailable);
	});
      } else {
        callback(null, btcAvailable, jpyAvailable);
      }
    },
    function(btcAvailabe, jpyAvailable, callback) {
      var bestBid = parseInt(cache.get("best_bid"));
      var bestAsk = parseInt(cache.get("best_ask"));
      var spread = (bestBid + bestAsk) * 0.5 * spreadPercentage;
      var buyPrice = parseInt(bestBid - spread);
      var sellPrice = parseInt(bestAsk + spread);

      if(btcAvailable > maxHoldBtc) {
        callback("BTC amount is over the threthold.", null);
      }

      if(btcAvailable > orderAmount) {
        console.log("--- sell order --- ", sellPrice, orderAmount);
	api.order(pair, sellPrice, orderAmount, "sell", "limit").then(function(orderRes) {
	  // console.log(orderRes);
	});  
      }

      if(jpyAvailable > buyPrice * orderAmount) {
        console.log("--- buy order ---", buyPrice, orderAmount);
	api.order(pair, buyPrice, orderAmount, "buy", "limit").then(function(orderRes) {
	  // console.log(orderRes);
	});     
      }
    }
  ],
  function(err, results) {
    if(err){
      console.log("[ERROR]" + err);
    }
  });
};



