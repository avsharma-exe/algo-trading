from kite_instance import kite
from time import sleep

squareoff = None

def place_order(order,acc_token):
  global squareoff
  print(order)
  kite.set_access_token(acc_token)
  print(order.derivative_name)
  d_quote = 'NFO:'+order.derivative_name
  dltp = kite.quote([d_quote])
  print(dltp[d_quote]['last_price'])
  quantity_unround = order.capital/dltp[d_quote]['last_price']
  quantity = 50 * round(quantity_unround/50)
  if quantity > quantity_unround:
    quantity = quantity - 50
  print(quantity,quantity_unround)
  if quantity > 1800:
    quantity = 1800
  lastprice = float(dltp[d_quote]['last_price'])
  squareoff = lastprice + ((float(order.squareoff)/100)*lastprice)
  squareoff = round(squareoff * 2) / 2
  print("Last Price: ",lastprice," Selling Price .25%: ", squareoff )
  try:
      order_id = kite.place_order(tradingsymbol=order.derivative_name,\
      price=lastprice,variety=kite.VARIETY_REGULAR,\
      exchange=kite.EXCHANGE_NFO,transaction_type=kite.TRANSACTION_TYPE_BUY,\
      quantity=quantity,order_type=kite.ORDER_TYPE_LIMIT,\
      product=kite.PRODUCT_NRML)
      sleep(1)

      print("Order placed. ID is : {} and {}".format(order_id))
  except Exception as e:
      print("Order placement failed:",e)

def place_sell_order(data,acc_token):
  global squareoff
  if not squareoff:
    squareoff = data[2] + ((1.5/100)*data[2])
    squareoff = round(squareoff * 2) / 2
  kite.set_access_token(acc_token)
  order_id_s = kite.place_order(tradingsymbol=data[0],\
      price=squareoff,variety=kite.VARIETY_REGULAR,\
      exchange=kite.EXCHANGE_NFO,transaction_type=kite.TRANSACTION_TYPE_SELL,\
      quantity=data[1],order_type=kite.ORDER_TYPE_LIMIT,\
      product=kite.PRODUCT_NRML)
  print("Order placed. ID is : {} and {}".format(order_id_s))
