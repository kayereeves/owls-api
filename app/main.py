#based on
#https://www.bogotobogo.com/python/python-REST-API-Http-Requests-for-Humans-with-Flask.php
#https://www.nintyzeros.com/2019/11/flask-mysql-crud-restful-api.html

import json
import re
import pandas as pd
from flask import Flask, request, jsonify, make_response, current_app, abort
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://owls:vHAxYRzjZYSEr6E@owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com/owls'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

###Models####
class Transaction(db.Model):
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

class ItemData(db.Model):
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

db.create_all()

class TransactionSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Transaction
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

class ItemDataSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = ItemData
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

@app.route('/', methods = ['GET'])
def index():
    return current_app.send_static_file('index.html')

#submit a trade to the db
@app.route('/transactions/submit', methods = ['GET','POST'])
def submit_trade():
    data = request.get_json()
    transaction_schema = TransactionSchema()
    transaction = transaction_schema.load(data)
    t = Transaction.create(transaction)
    result = transaction_schema.dump(t)

    return make_response(jsonify({"transaction": result}),200)

#return results for trades containing an item
#user_id is deliberately omitted from result
@app.route('/transactions/<string:item>', methods = ['GET'])
def get_by_item(item):
    start = request.args.get('start', default='1900-01-01', type=str)
    end = request.args.get('end', default='2100-01-01', type=str)
    item = item.casefold()

    get_transactions = Transaction.query.all()
    transaction_schema = TransactionSchema(many=True)
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

#retrieve owls guide value for an item by name
@app.route('/itemdata/<string:item>', methods = ['GET'])
def get_owls_value(item):
    item = item.casefold()
    get_itemdata = ItemData.query.get(item)
    
    if (get_itemdata):
        itemdata_schema = ItemDataSchema()
        itemdata = itemdata_schema.dump(get_itemdata)

        return make_response(jsonify({"owls_value": itemdata['owls_value'], "last_updated": itemdata['date_of_last_update']}))
    else:
        abort(404)

#retrieve item name and value pairs in format expected by the owls userscript
@app.route('/itemdata/owls_script/', methods = ['GET'])
def owls_script():
    get_itemdata = ItemData.query.all()
    itemdata_schema = ItemDataSchema(many=True)
    itemdata = itemdata_schema.dump(get_itemdata)
    name_list = []
    value_list = []

    for data in itemdata:
        name_list.append(data['api_name'])
        value_list.append(data['owls_value'])

    result = dict(zip(name_list, value_list))

    return make_response(jsonify(result))