#based on
#https://www.bogotobogo.com/python/python-REST-API-Http-Requests-for-Humans-with-Flask.php
#https://www.nintyzeros.com/2019/11/flask-mysql-crud-restful-api.html

from __future__ import print_function
import json
import os
import re
import pandas as pd
import dateutil
import hashlib
import bcrypt
import os.path
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Flask, request, jsonify, make_response, current_app, abort, session, send_from_directory
from flask.sessions import SecureCookieSessionInterface
from flask_login import *
from flask_sqlalchemy import SQLAlchemy
from flask_openid import OpenID
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import fields
from flask_cors import CORS
from datetime import datetime
from .secret import SECRET_KEY, DB_USER, DB_PASS, DB_URL

#init app
app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

#init login manager
app.secret_key = SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)
session_cookie = SecureCookieSessionInterface().get_signing_serializer(app)
#allow CORS
CORS(app)
#init database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + DB_USER + ':' + DB_PASS + '@' + DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#oid = OpenID(app, db, safe_roots=[])
#Models and Schema
#Transaction
class _Transaction(db.Model):
    __tablename__ = "transactions"
    loaded_at = db.Column(db.Date)
    transaction_id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(255))
    traded = db.Column(db.String(4096))
    traded_for = db.Column(db.String(4096))
    ds = db.Column(db.Date)
    notes = db.Column(db.String(4096))
    def create(self):
      db.session.add(self)
      db.session.commit()
      return self
    def __init__(self,loaded_at,user_id,traded,traded_for,ds,notes):
        self.loaded_at = loaded_at
        self.transaction_id = "new"
        self.user_id = user_id
        self.traded = traded
        self.traded_for = traded_for
        self.ds = ds
        self.notes = notes
class _TransactionSchema(SQLAlchemyAutoSchema):
    class _Meta(SQLAlchemyAutoSchema.Meta):
        model = _Transaction
        sqla_session = db.session
        include_relationships = True
        load_instance = True
    loaded_at = fields.String(required=False)
    transaction_id = fields.String(dump_only=True, required=False)
    user_id = fields.String(required=False)
    traded = fields.String(required=True)
    traded_for = fields.String(required=True)
    ds = fields.String(required=False)
    notes = fields.String(required=False)
#Models and Schema
#ItemData
class _ItemData(db.Model):
    __tablename__ = "itemdata"
    name = db.Column('Item', db.String(70))
    retirement = db.Column('retirement date', db.String(10))
    release_type = db.Column('cap, LT buyable or RR', db.String(10))
    num_reports = db.Column('# of reports', db.String(10))
    values_reported = db.Column('values reported', db.String(500))
    old_reports = db.Column('old reports', db.String(500))
    owls_value = db.Column('last Owls value', db.String(100))
    date_of_last_update = db.Column('last updated', db.String(20))
    api_name = db.Column('API name', db.String(70), primary_key=True)
    def create(self):
      db.session.add(self)
      db.session.commit()
      return self
    def __init__(self,name,retirement,release_type,num_reports,values_reported,old_reports,owls_value,date_of_last_update,api_name):
        self.name = name
        self.retirement = retirement
        self.release_type = release_type
        self.num_reports = num_reports
        self.values_reported = values_reported
        self.old_reports = old_reports
        self.owls_value = owls_value
        self.date_of_last_update = date_of_last_update
        self.api_name = api_name
class _ItemDataSchema(SQLAlchemyAutoSchema):
    class _Meta(SQLAlchemyAutoSchema.Meta):
        model = _ItemData
        sqla_session = db.session
    name = fields.String(required=True)
    retirement = fields.String(required=False)
    release_type = fields.String(required=False)
    num_reports = fields.String(required=False)
    values_reported = fields.String(required=False)
    old_reports = fields.String(required=False)
    owls_value = fields.String(required=False)
    date_of_last_update = fields.String(required=False)
    api_name = fields.String(required=True)
#Models and Schema
#Terms
class _Terms(db.Model):
    __tablename__ = "terms_users"
    user_id = db.Column(db.String(255), primary_key=True)
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def __init__(self, user_id):
        self.user_id = user_id
class _TermsSchema(SQLAlchemyAutoSchema):
    class _Meta(SQLAlchemyAutoSchema.Meta):
        model = _Terms
        sqla_session = db.session
        include_relationships = True
        load_instance = True
    user_id = fields.String(required=False)
#Models and Schema
#UserData
class _UserData(db.Model):
    __tablename__ = "userdata"
    username = db.Column(db.String(20), primary_key=True)
    hash = db.Column(db.String(60))
    email = db.Column(db.String(50))
    isAdmin = db.Column(db.Boolean)
    def create(self):
        db.session.add(self)
        db.session.commit()
        return self
    def __init__(self, username, hash, email, isAdmin):
        self.username = username
        self.hash = hash
        self.email = email
        self.isAdmin = isAdmin
class _UserDataSchema(SQLAlchemyAutoSchema):
    class _Meta(SQLAlchemyAutoSchema.Meta):
        model = _UserData
        sqla_session = db.session
        include_relationships = True
        load_instance = True
    username = fields.String(required=True)
    hash = fields.String(required=True)
    email = fields.String(required=True)
    isAdmin = fields.Boolean(required=True)

with app.app_context():
    db.create_all()
    
#routes
@app.route('/', methods = ['GET'])
def index():
    return current_app.send_static_file('index.html')
"""
Submit a trade to the database.
Accepts a trade in the format {"loaded_at": "", "user_id": "", "traded": "", "traded_for": "", "ds": "", "notes": ""}
/transactions/submit
"""
@app.route('/transactions/submit', methods = ['GET','POST'])
def submit_trade():
    data = request.get_json()
    #print(data)
    #transaction_schema = _TransactionSchema()
    #transaction = transaction_schema.loads(data)
    #t = _Transaction.create(transaction)
    t = _Transaction(loaded_at=data['loaded_at'], user_id=data['user_id'], traded=data['traded'], traded_for=data['traded_for'],
    ds=data['ds'], notes=data['notes'])
    db.session.add(t)
    db.session.commit()
    #result = transaction_schema.dump(t)
    result = data
    return make_response(jsonify({"transaction": result}),200)
"""
Return data for trades containing an item by name.
/transactions/<string:item>
"""
#user_id is deliberately omitted from result
@app.route('/transactions/<string:item>', methods = ['GET'])
def get_by_item(item):
    start = request.args.get('start', default='1900-01-01', type=str)
    end = request.args.get('end', default='2100-01-01', type=str)
    item = item.casefold()
    get_transactions = _Transaction.query.all()
    transaction_schema = _TransactionSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    resultList = []
    for i,q in enumerate(transaction):
        transaction_str = ''
        if item in q['traded'].casefold():
            transaction_str = q['traded'].casefold()
        elif item in q['traded_for'].casefold():
            transaction_str = q['traded_for'].casefold()
        if re.search("Dyeworks .*: ".casefold() + item, transaction_str):
            pass
        elif transaction_str == '':
            pass
        else:
            if (transaction[i]['ds'] == '0000-00-00'):
                transac_date = datetime.strptime(start, '%Y-%m-%d')
            else:
                transac_date = datetime.strptime(transaction[i]['ds'], '%Y-%m-%d')
            
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            if transac_date >= start_date and transac_date <= end_date:
                del transaction[i]['user_id'] 
                del transaction[i]['transaction_id']
                del transaction[i]['loaded_at']
                resultList.append(transaction[i])
    return make_response(jsonify({"results": resultList}))
"""
Retrieve ~Owls guide value for an item by name.
/itemdata/<string:item>
"""
@app.route('/itemdata/<string:item>', methods = ['GET'])
def get_owls_value(item):
    item = item.casefold()
    get_itemdata = _ItemData.query.get(item)
    
    if (get_itemdata):
        itemdata_schema = _ItemDataSchema()
        itemdata = itemdata_schema.dump(get_itemdata)
        return make_response(jsonify({"owls_value": itemdata['owls_value'], "last_updated": itemdata['date_of_last_update']}))
    else:
        abort(404)
"""
Retrieve ~Owls guide value and trade data for an item by name.
/itemdata/profile/<string:item>
"""
@app.route('/itemdata/profile/<string:item>', methods = ['GET'])
def get_item_profile(item):
    item = item.casefold()
    get_itemdata = _ItemData.query.get(item)

    if (get_itemdata):
        itemdata_schema = _ItemDataSchema()
        itemdata = itemdata_schema.dump(get_itemdata)

        start = request.args.get('start', default='1900-01-01', type=str)
        end = request.args.get('end', default='2100-01-01', type=str)
        #todo: write new regex
        regex = ".* \+ " + item + " (.*) \+ .*|" + item + " (.*).*|" + ".* \+ " + item + " (.*)"

        get_transactions = _Transaction.query.all()
        transaction_schema = _TransactionSchema(many=True)
        transaction = transaction_schema.dump(get_transactions)
        trades = []

        for i,q in enumerate(transaction):
            transaction_str = ''

           # if item in q['traded'].casefold():
            if re.match(regex, q['traded'].casefold()):
                transaction_str = q['traded']
            if re.match(regex, q['traded_for'].casefold()):
                transaction_str = q['traded_for']

            if len(transaction_str) > 0:
                del transaction[i]['user_id'] 
                del transaction[i]['transaction_id']
                del transaction[i]['loaded_at']
                trades.append(transaction[i])

        trades.reverse()

        #limit to 20 results?
        print(itemdata['owls_value'])
        print(itemdata['date_of_last_update'])
        print(len(trades))

        return make_response(jsonify({"guide_value": itemdata['owls_value'], "last_updated": itemdata['date_of_last_update'], "trade_reports": trades}))
    else:
        abort(404)

"""
Retrieve all item name and value pairs in format expected by the ~Owls userscript.
/itemdata/owls_script
"""
@app.route('/itemdata/owls_script/', methods = ['GET'])
def owls_script():
    get_itemdata = _ItemData.query.all()
    itemdata_schema = _ItemDataSchema(many=True)
    itemdata = itemdata_schema.dump(get_itemdata)
    name_list = []
    value_list = []
    for data in itemdata:
        name_list.append(data['api_name'])
        value_list.append(data['owls_value'])
    result = dict(zip(name_list, value_list))
    return make_response(jsonify(result))
"""
Checks if a user has read the T&C.
/terms/<string:user>
"""
@app.route('/terms/<string:user>', methods = ['GET'])
def terms_check(user):
    get_user = _Terms.query.get(user)
    
    if not (get_user):
        abort(404)
    return user
"""
Adds a user to the list of users who have read the T&C.
/terms/add/<string:user>
"""
@app.route('/terms/add/<string:user>', methods = ['GET', 'POST'])
def terms_add(user):
    data = _Terms(user)
    db.session.add(data)
    db.session.commit()
    return user
"""
OwlBot Thumbnail Dispenser
"""
@app.route('/images/bot_thumb', methods = ['GET'])
def bot_thumb():
    return current_app.send_static_file('owls_thumb.png')

"""
OwlBot Rainbow Thumbnail Dispenser
"""
@app.route('/images/bot_thumb_pride', methods = ['GET'])
def bot_thumb_pride():
    return current_app.send_static_file('owls_thumb_rainbow.png')

#adds a new user to the database
#@app.route('/register', methods = ['GET'])
def register():
    return current_app.send_static_file('register.html')
#@app.route('/register_request', methods = ['GET', 'POST'])
def register_request():
    data = request.get_json()
    if not (_UserData.query.get(data['user']) or _UserData.query.filter_by(email=data['email']).first()):
        hashed = bcrypt.hashpw(data['pass'].encode('utf8'), bcrypt.gensalt())
        new_user = _UserData(username=data['user'], hash=hashed, email=data['email'], isAdmin=False)
        db.session.add(new_user)
        db.session.commit()
        #log the new user in
        session['username'] = data['user']
        return "REGISTER_SUCCESS"
    
    return "REGISTER_FAIL: EXISTING USER"
#logs an existing user in
#@app.route('/login', methods = ['GET'])
def login_page():
    return current_app.send_static_file('login.html')
#@app.route('/login_request', methods = ['GET', 'POST'])
def login_request():
    data = request.get_json()
    user_data = _UserData.query.get(data['user'])
    if bcrypt.checkpw(data['pass'].encode('utf8'), user_data.__dict__['hash'].encode('utf8')):
        #log in
        session['username'] = data['user']
        print(session['username'])
        print("LOGIN_SUCCESS")
        return "LOGIN_SUCCESS"
    #generate failure message
    return "LOGIN_FAILURE"
#@app.route('/login_request_email', methods = ['GET', 'POST'])
def login_request_email():
    data = request.get_json()
    user_data = _UserData.query.filter_by(email=data['user']).first()
    if bcrypt.checkpw(data['pass'].encode('utf8'), user_data.__dict__['hash'].encode('utf8')):
        #log in
        session['username'] = user_data['username']
        print("LOGIN_SUCCESS")
        return "LOGIN_SUCCESS"
    #generate failure message
    return "LOGIN_FAILURE"
#form that allows a user to reset their password
#@app.route('/login_help', methods = ['GET'])
def login_help():
    return current_app.send_static_file('login_help.html')
#form that allows a user to reset their password
#@app.route('/login_help_request', methods = ['GET', 'POST'])
def login_help_request():
    data = request.get_json()
    user_data = _UserData.query.get(data['user'])
    email = user_data['email']
    #send an email allowing user to reset their password
#@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return current_app.send_static_file('index.html')
#@app.route('/user_request')
def getCurrentUser():
    if 'username' in session.keys():
        return session['username']
    return 'Guest'