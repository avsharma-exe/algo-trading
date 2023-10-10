from kiteticker_func import on_close, on_connect, on_error, on_ticks, setData, order_update
from threading import Thread
import threading
from time import sleep
from kite_instance import kiteTickerInstance

kws = None
threadname = None
def background_task():
  global kws
  kws.connect(threaded=True)

def order_process(data, acc_token):
  global kws, threadname
  kws = kiteTickerInstance(acc_token)
  setData(data, acc_token)
  # Assign the callbacks.
  kws.on_ticks = on_ticks
  kws.on_connect = on_connect
  kws.on_close = on_close
  kws.on_error = on_error
  kws.on_order_update = order_update
  kws.connect(threaded=True)

def close_process():
  global kws
  print('in close process')
  sleep(10)
  kws.close(1000,"Manual close")
