

PStrategy StrategyExternal::createStrategy(const std::string_view &id, json:Value config) {
  return new Strategy(*this, id, config, json::object);
}

StrategyExternal::Strategy::Strategy(StrategyExternal &owner,
		const std::string_view id, json::Value config, json::Value state)
	:owner(owner),config,state(state),id(id)
{
  
}

bool StrategyExternal::Strategy::isValid() const {
  return owner.jsonRequestExchange("isValid", rqHdr()).getBool();
}

PStrategy StrategyExternal::Strategy::onIdle(
		const IStockApi::MarketInfo &minfo, const IStockApi::Ticker &curTicker,
		double assets, double currency) const {
  
  json::Value st = owner.jsonRequestExchange("onIdle", reqHdr()
         ("minfo",toJSON(minfo))
         ("ticker",toJSON(minfo))
         ("assets",assets)
	 ("currency", currency));
  return new Strategy(owner,id,config,st);
}

std::pair<IStrategy::OnTradeResult, PStrategy> StrategyExternal::Strategy::onTrade(
	const IStockApi::MarketInfo &mifo, double tradePrice, double tradeSize,
	double assetsLeft, double currencyLeft) const {
  
  json::Value res = owner.jsonRequestExchange("onTrade", reqHdr()
	  ("minfo",toJSON(minfo))
	  ("price", tradePrice)
	  ("size",tradeSize)
	  ("assets", assetsLeft)
	  ("currency", currencyLeft));

  json::Value st = res["state"];
  OnTradeResult rp;
  rp.normAccum = res["norm_accum"].getNumber();
  rp.normProfit = res["norm_profit"].getNumber();

  return {
    rp,
    new Strategy(owner,id, config,st)
  };

}

json::Value StrategyExternal::Strategy::exportState() const {
  return state;
}

PStrategy StrategyExternal::Strategy::importState(json::Value src) const {
  return new Strategy(owner, id, config, src);
}

StrategyExternal::Strategy::OrderData StrategyExternal::Strategy::getNewOrder(
    const IStockApi::MarketInfo &minfo, double new_price, double dir,
    double assets, double currency) const {

  json::Value ord = owner.jsonRequestExchange("getNewOrder",reqHdr()
		  ("minfo",toJSON(minfo))
		  ("new_price", new_price)
		  ("dir",assets)
		  ("assets",assets)
		  ("currency", currency));
  return OrderDate {
    ord["price"].getNumber(),
    ord["size"].getNumber()
  };
}
























