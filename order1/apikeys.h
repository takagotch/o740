
#ifndef SRC_MAIN_APIKEYS_H_
#define SRC_MAIN_APIKEYS_H_
#include <imtjson/value.h>

class IApiKey {
public:

  virtual void seApiKey(json::Value keyData) = 0;

  virtual json::Value getApiKeyFields() const = 0;
};

#endif

