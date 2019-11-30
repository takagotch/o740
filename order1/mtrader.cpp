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














