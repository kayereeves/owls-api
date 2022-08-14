#based on
#https://www.bogotobogo.com/python/python-REST-API-Http-Requests-for-Humans-with-Flask.php
#https://www.nintyzeros.com/2019/11/flask-mysql-crud-restful-api.html

import json
import pandas as pd
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://owls:vHAxYRzjZYSEr6E@owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com/owls'
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

    def __init__(self,loaded_at,transaction_id,user_id,traded,traded_for,ds,notes):
        self.loaded_at = loaded_at
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.traded = traded
        self.traded_for = traded_for
        self.ds = ds
        self.notes = notes

    def __repr__(self):
        return '' % self

class ItemData(db.Model):
    __tablename__ = "itemdata"
    name = db.Column('Item', db.String(70), primary_key=True)
    retirement = db.Column('retirement date', db.String(10))
    release_type = db.Column('cap, LT buyable or RR', db.String(10))
    num_reports = db.Column('# of reports', db.String(10))
    values_reported = db.Column('values reported', db.String(500))
    old_reports = db.Column('old reports', db.String(500))
    owls_value = db.Column('last Owls value', db.String(100))
    date_of_last_update = db.Column('last updated', db.String(20))

    def create(self):
      db.session.add(self)
      db.session.commit()
      return self

    def __init__(self,name,retirement,release_type,num_reports,values_reported,old_reports,owls_value,date_of_last_update):
        self.name = name
        self.retirement = retirement
        self.release_type = release_type
        self.num_reports = num_reports
        self.values_reported = values_reported
        self.old_reports = old_reports
        self.owls_value = owls_value
        self.date_of_last_update = date_of_last_update

    def __repr__(self):
        return '' % self

db.create_all()

class TransactionSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Transaction
        sqla_session = db.session
    loaded_at = fields.String(required=False)
    transaction_id = fields.String(dump_only=True)
    user_id = fields.String(required=False)
    traded = fields.String(required=True)
    traded_for = fields.String(required=True)
    ds = fields.String(required=False)
    notes = fields.String(required=False)

class ItemDataSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = ItemData
        sqla_session = db.session
    name = fields.String(required=True, primary_key=True)
    retirement = fields.String(required=False)
    release_type = fields.String(required=False)
    num_reports = fields.String(required=False)
    values_reported = fields.String(required=False)
    old_reports = fields.String(required=False)
    owls_value = fields.String(required=False)
    date_of_last_update = fields.String(required=False)

#@app.route('/transactions', methods = ['GET'])
def index():
    get_transactions = Transaction.query.all()
    transaction_schema = TransactionSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    return make_response(jsonify({"transaction": transaction}))

#return results by user id
#will likely be disabled to prevent abuse
#@app.route('/transactions/user/<string:user>', methods = ['GET'])
def get_by_user(user):
    user = user.casefold()
    get_transactions = Transaction.query.all()
    transaction_schema = TransactionSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    resultList = []

    for i,q in enumerate(transaction):
        if q['user_id'].casefold() == user:
            resultList.append(transaction[i])

    return make_response(jsonify({"transaction": resultList}))

#return results for trades containing an item name
#@app.route('/transactions/item/<string:item>', methods = ['GET'])
def get_by_item(item):
    item = item.casefold()
    get_transactions = Transaction.query.all()
    transaction_schema = TransactionSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    resultList = []

    for i,q in enumerate(transaction):
        if item in q['traded'].casefold() or item in q['traded_for'].casefold():
            resultList.append(transaction[i])

    return make_response(jsonify({"transaction": resultList}))

#@app.route('/itemdata', methods = ['GET'])
def itemdata_index():
    get_itemdata = ItemData.query.all()
    itemdata_schema = ItemDataSchema(many=True)
    itemdata = itemdata_schema.dump(get_itemdata)
    return make_response(jsonify({"itemdata": itemdata}))

#@app.route('/itemdata/owlsvalue/<string:item>', methods = ['GET'])
def get_owls_value(item):
    item = item.casefold()
    get_itemdata = ItemData.query.all()
    itemdata_schema = ItemDataSchema(many=True)
    itemdata = itemdata_schema.dump(get_itemdata)
    return make_response(jsonify({"owls value": itemdata}))

@app.route('/itemdata/owls_script/', methods = ['GET'])
def owls_script():
    get_itemdata = ItemData.query.all()
    itemdata_schema = ItemDataSchema(many=True)
    itemdata = itemdata_schema.dump(get_itemdata)
    name_list = []
    value_list = []

    for data in itemdata:
        name_list.append(data['name'])
        value_list.append(data['owls_value'])

    result = dict(zip(name_list, value_list))

    return make_response(jsonify(result))

#run
if __name__ == "__main__":
    app.run('0.0.0.0', port=443, ssl_context=('adhoc'))