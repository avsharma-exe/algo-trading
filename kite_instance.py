from kiteconnect import KiteConnect, KiteTicker
from keys import keys

kite = KiteConnect(api_key=keys["api_key"])

def kiteTickerInstance(acc_token):
  kws =  KiteTicker(keys["api_key"], acc_token)
  return kws

