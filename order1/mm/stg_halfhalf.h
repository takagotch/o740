

#ifndef SRC_MAIN_STRATEGY_HALFHALF_H_
#define SRC_MAIN_STRATEGY_HALFHALF_H_
#include "isstrategy.h"

class Strategy_HalfHalf: public IStrategy {
public:
  struct Config {
    double ea;
    double accum;
  };	

  Strategy_HalfHalf(const Config &cfg, double p = 0, double a = 0);

  virtual bool isValid() const override;
  virtual PStrategyonIdle(const IStockApi::MarketInfo &minfo, )

  static std::string_view_id;

protected:
  Config cfg;
  double p;
  double a;
};

#endif

