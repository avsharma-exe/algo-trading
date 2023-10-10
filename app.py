from flask import Flask, render_template, request, redirect
from kiteconnect import KiteConnect, connect
from kiteconnect import KiteTicker
from dotenv import dotenv_values
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from threading import Thread
import threading
import logging
from time import sleep
from pprint import pprint


app = Flask(__name__)
# Database creation code for sqlAlchemy - go to terminal enter python, from app import db, db.create_all()

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./data/acc_tkn.db"
app.config['SQLALCHEMY_BINDS'] = {'orders' : "sqlite:///./data/orders.db"}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Classes for schema declaration of tables

# Class for access token table
class Acc_token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(40), nullable = False)
    date_created = db.Column(db.Date, default = date.today() )

    def __repr__(self) -> str:
        return f"{self.access_token} - {self.date_created}"

# Class for Orders table
class Orders(db.Model):
    __bind_key__ = 'orders'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False)
    ins_token = db.Column(db.Integer, nullable = False)
    derivative_name = db.Column(db.String(40), nullable = False)
    derivative_ins_token = db.Column(db.Integer, nullable = False)
    capital = db.Column(db.Float, nullable = False)
    action = db.Column(db.String(5), nullable = False)
    trigger_price = db.Column(db.Float, nullable = False)
    quantity = db.Column(db.Integer, nullable = True)
    squareoff = db.Column(db.Integer, nullable = True)
    stoploss = db.Column(db.Integer, nullable = True)
    status = db.Column(db.Boolean, nullable = False)
    date_created = db.Column(db.Date, default = date.today() )



    def __repr__(self) -> str:
        return f"{self.name} - {self.ins_token} - {self.derivative_name} \
         - {self.derivative_ins_token} - {self.trigger_price} "

# Kite connect connection here

keys = dotenv_values(".env")
request_token = ""
access_token = ""
kite = KiteConnect(api_key=keys["api_key"])
kws = None
y_date = date.today() -  timedelta(days = 1) #Yesterdays date to delete older data
data = []
tick_data = []
connection = False

def background_task():
    kws.connect(threaded=True)




def on_ticks(ws, ticks):
    global kite, access_token
    kite.set_access_token(access_token)
    for single_instrument in ticks:
      ltp = single_instrument['last_price']
      print(ltp)
      for order in data:
        # print('order token -',order.ins_token,'single ins - ',single_instrument['instrument_token'])
        if order.ins_token == single_instrument['instrument_token']:
          if order.action == 'long'  and ltp <= order.trigger_price:
            print(order.trigger_price)
            # print(order.derivative_name)
            d_quote = 'NFO:'+order.derivative_name
            dltp = kite.quote([d_quote])
            print(dltp[d_quote]['last_price'])
            quantity_unround = order.capital/dltp[d_quote]['last_price']
            quantity = 50 * round(quantity_unround/50)
            if quantity > quantity_unround:
              quantity = quantity - 50
            print(quantity,quantity_unround)
            try:
                order_id = kite.place_order(tradingsymbol=order.derivative_name,\
                price=dltp[d_quote]['last_price'],variety=kite.VARIETY_REGULAR,\
                exchange=kite.EXCHANGE_NFO,transaction_type=kite.TRANSACTION_TYPE_BUY,\
                quantity=quantity,squareoff=1.5,stoploss=1,order_type=kite.ORDER_TYPE_MARKET,\
                product=kite.PRODUCT_MIS)
                sleep(1)
                print("Order placed. ID is: {}".format(order_id))
            except Exception as e:
                print("Order placement failed:",e)

        if order.action == 'short'  and ltp >= order.trigger_price:
            # print(order.derivative_name)
            d_quote = 'NFO:'+order.derivative_name
            dltp = kite.quote([d_quote])
            print(dltp[d_quote]['last_price'])
            quantity_unround = order.capital/dltp[d_quote]['last_price']
            quantity = 50 * round(quantity_unround/50)
            if quantity > quantity_unround:
              quantity = quantity - 50
            print(quantity,quantity_unround)
            try:
                order_id = kite.place_order(tradingsymbol=order.derivative_name,\
                price=dltp[d_quote]['last_price'],variety=kite.VARIETY_REGULAR,\
                exchange=kite.EXCHANGE_NFO,transaction_type=kite.TRANSACTION_TYPE_BUY,\
                quantity=quantity,squareoff=1.5,stoploss=1,order_type=kite.ORDER_TYPE_MARKET,\
                product=kite.PRODUCT_MIS)
                sleep(1)
                print("Order placed. ID is: {}".format(order_id))
            except Exception as e:
                print("Order placement failed:",e)
    pprint(ticks)

def on_connect(ws, response):
    global connection
    print('tick data to be subscribed - ',tick_data)
    ws.subscribe(tick_data)
    ws.set_mode(ws.MODE_LTP,tick_data)

def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

def on_error(ws, code, reason):
    logging.error("closed connection on error: {} {}".format(code, reason))





@app.route("/")
def login():
    global access_token, y_date, kite
    now = date.today() #taking todays date
    url = kite.login_url() #Url for kite login to get access token

    check_validity = Acc_token.query.all()

    if len(check_validity) == 1:
      last_token_date = check_validity[0].date_created
      if last_token_date == now :
        access_token = check_validity[0].access_token
        return redirect("/placeorder")
      else:
        Acc_token.query.filter_by(date_created=y_date).delete()
        db.session.commit()
        return redirect(url)
    else:
      return redirect(url)


@app.route("/request")
def order():
    global request_token, access_token
    request_token = request.args.get('request_token')
    data = kite.generate_session(request_token, api_secret=keys["api_secret"])
    access_token = (data["access_token"])
    kite.set_access_token(data["access_token"])
    acc_tkn = Acc_token(access_token=access_token)
    db.session.add(acc_tkn)
    db.session.commit()
    return redirect('/placeorder')

@app.route("/placeorder")
def placeorder():
    global access_token, connection
    orders_table = Orders.query.all()
    if not access_token:
      print('inside nione')
      return redirect('/')
    print(connection)
    return render_template('/place_order/index_copy.html',orders_table = orders_table,\
      connection = connection)

@app.route("/delete/<int:sno>")
def deleteorder(sno):
    deleting_order = Orders.query.filter_by(id=sno).first()
    db.session.delete(deleting_order)
    db.session.commit()
    return redirect('/placeorder')

@app.route("/close_loop")
def close_loop():
    global kws
    kws.close()
    return redirect('/placeorder')


@app.route("/update/<int:sno>", methods=['GET','POST'])
def updateorder(sno):
    updating_order = Orders.query.filter_by(id=sno).first()
    if request.method == 'POST':
      capital = request.form['capital']
      entry_price = request.form['entry_price']
      stop_loss = request.form['stop_loss']
      square_off = request.form['square_off']
      action = request.form['action']
      status = request.form['status']
      updating_order.capital = capital
      updating_order.action = action
      updating_order.trigger_price = entry_price
      updating_order.squareoff = square_off
      updating_order.stoploss = stop_loss
      updating_order.status = eval(status)
      db.session.add(updating_order)
      db.session.commit()
      return redirect('/placeorder')
    updating_order = Orders.query.filter_by(id=sno).first()
    db.session.commit()
    return render_template('/place_order/update.html',order=updating_order)


@app.route("/postorder",methods=['POST'])
def postorder():

    pname = request.form['parent_name']
    pstockId = request.form['parent_id']
    cname = request.form['derivative_name']
    cstockId = request.form['derivative_id']
    capital = request.form['capital']
    trigger_price = request.form['entry_price']
    squareoff = request.form['square_off']
    stoploss = request.form['stop_loss']
    action = request.form['action']

    orderQuery = Orders(name=pname, ins_token=pstockId, derivative_name=cname,
                        derivative_ins_token=cstockId,capital=capital,action=action,
                        trigger_price=trigger_price,squareoff=squareoff,stoploss=stoploss,
                        status=False,quantity='null')

    db.session.add(orderQuery)
    db.session.commit()
    print('data commited')
    return redirect('/placeorder')

@app.route("/startloop")
def startloop():
      global kws, access_token, tick_data, data, connection
      tick_data = []
      kws = None
      orders = Orders.query.all()
      print(orders)
      for order in orders:
        tick_data.append(order.ins_token)
      print(tick_data)

      kws =  KiteTicker(keys["api_key"], access_token)

      # Assign the callbacks.
      kws.on_ticks = on_ticks
      kws.on_connect = on_connect
      kws.on_close = on_close
      kws.on_error = on_error
      print('acc',access_token)
      print(connection)
      ticker_thread = Thread(target=background_task)
      ticker_thread.daemon = True
      ticker_thread.start()
      return redirect('/placeorder')


if __name__ == "__main__":
    app.run(debug=True, port=8000)
