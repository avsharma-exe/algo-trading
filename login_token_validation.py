from flask import request
from kite_instance import kite
from datetime import date, timedelta
from keys import keys

y_date = date.today() -  timedelta(days = 1) #Yesterdays date to delete older data

def acc_validator(Acc_token, db):
  url = kite.login_url() #Url for kite login to get access token
  now = date.today() #taking todays date
  print(now)
  check_validity = Acc_token.query.all()
  print(check_validity,len(check_validity))
  if len(check_validity) == 1:
    print(check_validity[0].date_created,"date here")
    last_token_date = check_validity[0].date_created
    if last_token_date == now :
      access_token = check_validity[0].access_token
      return (access_token, False)
    else:
      Acc_token.query.delete()
      db.session.commit()
      return (url, True)
  else:
    print('here a')
    Acc_token.query.delete()
    db.session.commit()
    return (url, True)

def token_fetcher_from_url(Acc_token, db):
    request_token = request.args.get('request_token')
    data = kite.generate_session(request_token, api_secret=keys["api_secret"])
    access_token = (data["access_token"])
    kite.set_access_token(data["access_token"])
    acc_tkn = Acc_token(access_token=access_token)
    db.session.add(acc_tkn)
    db.session.commit()
    return(access_token)
