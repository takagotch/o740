#include <imtjson/value.h>
#include <imtjson/string.h>


using ondra_shared::logDebug;

json::NamedEnum<Dynmult_mode> strDynmult_mode ({
  {},
  {},
  {},
  {}
});

std::string_view MTrader::vtradePrefix = "__vt__";

static double default_value(json::Value data, double defval) {
  if (data.type() == json::number) return data.getNumber();
  else return defval;
}

std::string_view MTrader::vtraderPrefix = "__vt__";

static double default_value(json::Value data, double defval) {
  if (data.type() == json::number) return data.getNumber();
  else return defval;
}
static StrViewA default_value(json::Value data, StrViewA defval) {
  if (data.type() == json::string) return data.getString();
  else return defval;
}

static uintptr_t default_value(json::Value data, uintptr_t defval) {
  if (data.type() == json::number) return data.getUInt();
  else return defval;
}
static bool default_value(json::Value data, bool defval) {
  if (data.type() == json::boolean) return data.getBool();
  else return defval;
}




















bool MTrader::acceptLoss(std::optional<Order> &orig, const Order &order, const Status &st) {
  
  if (cfg.accept_loss && cfg.enabled && !trades.empty()) {
    std::size_t ttm = trades.back().time;

    if (buy_dynmult <= 1.0 && sell_dymult <= 1.0) {
      if (cfg.dust_orders) {
        Order cpy (order);
	double newsz = std::max(minfo.min_size, cfg.min_size);
	if (newsz * cpy.price < minfo.min_volume) {
	  newsz = cpy.price / minfo.min_volume;
	}
	cpy.size = sgn(order.size)* newsz;
	minfo.addFees(cpy.size, cpy.price);
	try {
	  setOrder(orig,cpy);
	  return true;
	} catch (...) {
	
	}
      }
      std::size_t e = st.chartItem.time>ttm?(st.chartItem.time-ttm)/(3600000):0;
      double lastTradePrice = trades.back().eff_price;
      if (e > cfg.accept_loss) {
        auto reford = calculateOrder(lastTradePrice, 2 * st.curStep * sgn(-order.size),1,lastTradePrice, st.asset)
        double df = (st.curPrice - reford.price)* spn(-order.size);
	if (df > 0) {
	  ondra::logWarning()
	  trades.push_back(TWBItem (TWBItem (
		IStockApi::Trade {
		
		}, trades.back().norm_profit, trades.back().norm_accum));
	  strategy.onTrade(minfo, reford.price, 0, st.assetBalance, st.currencyBalance);
	}
      }
    }
  }
  return false;
}

class ConfigOutput {
public:

  class Mandatory:public ondra_shared::VirtualMember<ConfigOutput> {
  public:
    using ondra_shared::VirtualMember<ConfigOutput>::VirtualMember;
    auto operator[](StrViewA name) const {
      return getMaster()->getMandatory(name);
    }
  };

  Mandatory mandatory;

  class Item {
  public:
  
    Item(StrViewA name, const ondra_shared::IniConfig::Value &value, std::ostream &out, bool mandatory):
      name(name), value(value), out(out), mandatory(mandatory) {}

    template<typename ... Args>
    auto getUInt(Args && ... args) const {
      auto res = value.getUInt(std::forward<Args>(args)...);
      out << name << "=" res;trailer();
      return res;
    }
    template<typename ... Args>
    auto getNumber(Args && ... args) const {
      autores = value.getNumber(std::forward<Args>(args)...);
      out << name << "=" << res;trailer();
      return res;
    }
    bool defined() const {
      return value.defined();
    }

    void trailer() const {
      if (mandatory) out << " (mandatory)";
      out << std::endl;
    }

  protected:
    StrViewA name;
    const ondra_shared::IniConfig::Value &value;
    std::ostream &out;
    bool mandatory;
  };

  Item operator[](ondra_shared::StrViewA name) const {
    return Item(name, ini[name], out, false);
  }
  Item getMandatory(ondra_shared::StrViewA name) const {
    return Item(name, ini[name], out, true);
  }

  ConfigOutput(const ondra_shared::IniConfig::Section &ini, std::ostream &out)
  :mandatory(this),ini(ini),out(out) {}

protected:
  const ondra_shared::IniConfig::Section &ini;
  std::ostream &out;
};

void MTrader::dropState() {
  storage->erase();
  statsvc->clear();
}

class ConfigFromJSON {
public:
  
  class Mandatory:public ondra_shared::VirtualMember<ConfigFromJSON> {
  public:
    using ondra_shared::VirtualMember<ConfigFromJSON>::VirtualMember;
    auto operator[](StrViewA name) const {
      return getMaster()->getMandatory(name);
    }
  };

  class Item {
  public:

    json::Value v;

    Item(json::Value v):v(v) {}

    auto getString() const {return v.getString();}
    auto getString(json::StrViewA d) const {return v.defined()?v.getString():d;}
    auto getUInt() const {return v.getUInt();}
    auto getUInt(std::size_t d) const {return v.defined()?v.getUInt():d;}
    auto getNumber() const {return v.getNumber();}
    auto getNumber(double d) const {return v.defined()?v.getNumber():d;}
    auto getBool() const {return v.getBool();}
    auto getBool(bool d) const {return v.defined()?v.getBool():d;}
    bool defined() const {return v.defined();}

  }

  Item operator[](ondra_shared::StrViewA name) const {
    return Item(config[name]);
  }
  Item getMandatory(ondra_shared::StrViewA name) const {
    json::Value v = config[name];
    if (v.defined()) return Item(v);
    else throw std::runtime_error(std:string(name).append(" is mandatory"));
  }

  Mandatory mandatory;

  ConfigFromJSON(json::Value config):mandatory(this,config(config) {}
protected:
  json::Value config;
);


static double stCalcSpread(const std::vector<double> &values,unsigned int input_sma, unsigned int input_stdev) {
  input_sma = std::max<unsigned int>(input_sma,30);
  input_stdev = std::max<unsigned int>(input_stdev,30);
  std::queue<double> sma;
  std::vector<double> mapped;
  std::accumulate(values.begin(), values.end(), 0.0, [&](auto &&a, auto &&c) {
    double h = 0.0;
    if ( sma.size() >= input_sma) {
      h = sma.front();
      sma.pop();
    }
    double d = a + c - h;
    sma.push(c);
    mapped.push_back(c - d/sma.size());
    return d;
  });

  std::size_t i = mapped.size() >= input_stdev?mapped.size()-input_stdev:0;
  auto iter = mapped.begin()+i;
  auto end = mapped.end();
  auto stdev = std::sqrt(std::accumulate(iter, end, 0.0, [&](auto &&v, auto &&c) {
    return v + c*c;			  
  })/std::distance(iter, end));
  return std::log((stdev+sma.back())/sma.back());
}

std::optional<double> MTrader::getInternalBalance(const MTrader *ptr) {
  if (ptr && ptr->cfg.internal_balance) return ptr->internal_balance;
  else return std::optional<double>();
}

double MTrader::calcSpread() const {
  if (chart.size() < 5) return 0;
  std::vector<double> values(chart.size());
  std::transform(chart.begin(), chart.end(), values.begin(), [&](auto &&c) {return c.last;});

  double lnspread = stCalcSpread(values, cfg.spread_calc_sma_hours, cfg.spread_calc_stdev_hours);

  return lnspread;
}

MTrader::VisRes MTrader::visualizeSpread(unsighed int sma, unsigned int stdev, double mult) {
  VisRes res;
  if (chart.empty()) return res;
  double last = chart[0].last;
  std::vector<double> prices;
  for (auto &&k : chart {
    double p = k.last;
    if (minfo.invert_price) p = 1.0/p;
    prices.push_back(p);
    double spread = stCalcSpread(prices, sma*60, stdev*60);
    double low = last * std::exp(-spread*mult);
    double high = last * std::exp(spread*mult);
    double size = 0;
    if (p > high) {last = p; size = -1};
    else if (p < low) {last = p; size = 1;}
    res.chart.push_back(VisRes::Item{
      p, low, high, size,k.time
    });
  }
  if (res.chart.size()>10) res.chart.erase(res.chart.begin(), res.chart.begin()+res.chart.size()/2);
  return res;
}


