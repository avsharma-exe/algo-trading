from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from login_token_validation import acc_validator, token_fetcher_from_url
from start_loop import close_process, order_process
import threading
import logging



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
    status = db.Column(db.Boolean, nullable = False)
    date_created = db.Column(db.Date, default = date.today() )



    def __repr__(self) -> str:
        return f"{self.name} - {self.ins_token} - {self.derivative_name} \
         - {self.derivative_ins_token} - {self.trigger_price} "

# Kite connect connection here

access_token = ""
data = []


@app.route("/")
def login():
  global access_token
  acc_token = acc_validator(Acc_token, db)
  print('here')
  if not acc_token[1]:
    access_token = acc_token[0]
    return redirect('/placeorder')
  else:
    return redirect(acc_token[0])


@app.route("/request")
def order():
    global access_token
    access_token = token_fetcher_from_url(Acc_token, db)
    return redirect('/placeorder')

@app.route("/placeorder")
def placeorder():
    global access_token, data
    print(threading.active_count())
    print('acc_token',access_token)
    if not access_token:
      return redirect('/')
    else:
      orders_table = Orders.query.all()
      data = orders_table
      return render_template('/place_order/index.html',orders_table = orders_table)

@app.route("/delete/<int:sno>")
def deleteorder(sno):
    deleting_order = Orders.query.filter_by(id=sno).first()
    db.session.delete(deleting_order)
    db.session.commit()
    return redirect('/placeorder')

@app.route("/close_loop")
def close_loop():
    close_process()
    return redirect('/placeorder')

@app.route("/update/<int:sno>", methods=['GET','POST'])
def updateorder(sno):
    updating_order = Orders.query.filter_by(id=sno).first()
    if request.method == 'POST':
      capital = request.form['capital']
      entry_price = request.form['entry_price']
      square_off = request.form['square_off']
      action = request.form['action']
      status = request.form['status']
      updating_order.capital = capital
      updating_order.action = action
      updating_order.trigger_price = entry_price
      updating_order.squareoff = square_off
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
    action = request.form['action']

    orderQuery = Orders(name=pname, ins_token=pstockId, derivative_name=cname,
                        derivative_ins_token=cstockId,capital=capital,action=action,
                        trigger_price=trigger_price,squareoff=squareoff,
                        status=False,quantity='null')

    db.session.add(orderQuery)
    db.session.commit()
    print('data commited')
    return redirect('/placeorder')

@app.route("/startloop")
def startloop():
  global data, access_token
  print('acc',access_token)
  print(data)
  order_process(data, access_token)
  return redirect('/loop_running')

@app.route("/loop_running")
def loop_running():
  return render_template('/order_loop/index.html')


if __name__ == "__main__":
    app.run(debug=True, port=8000)
