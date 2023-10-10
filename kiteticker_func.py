from time import sleep
from place_order import place_order, place_sell_order
from pprint import pprint
import logging

data = None
access_token = None

def setData(orders, acc_token):
  global data, access_token
  data = orders
  access_token = acc_token
  print(data)

def on_ticks(ws, ticks):
    global access_token
    for single_instrument in ticks:
      ltp = single_instrument['last_price']
      print(ltp)
      i = 0
      for order in data:
        if order.ins_token == single_instrument['instrument_token']:
          if order.action == 'long'  and ltp <= order.trigger_price and not(order.status):
            print("inside long")
            place_order(order,access_token)
            order.status = True
          elif order.action == 'short'  and ltp >= order.trigger_price and not(order.status):
            print("inside short")
            place_order(order,access_token)
            order.status = True
        print(len(data))
        print(i)
        # data.pop(i)
    pprint(ticks)

def on_connect(ws, response):
    global data
    tick_data = []
    for order in data:
      tick_data.append(order.ins_token)
    print('tick data to be subscribed - ',tick_data)
    ws.subscribe(tick_data)
    ws.set_mode(ws.MODE_LTP,tick_data)

def on_close(ws, code, reason):
    print('Disconnect',code,reason)
    sleep(1)

def on_error(ws, code, reason):
    logging.error("closed connection on error: {} {}".format(code, reason))

def order_update(ws, data):
  if data['transaction_type'] == 'BUY':
    print("inside if")
    if data['status'] == 'COMPLETE' :
      place_sell_order([data['tradingsymbol'],data['quantity'],data['price']],access_token)
  print("In Order update",data)

