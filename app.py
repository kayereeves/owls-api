#based on
#https://www.bogotobogo.com/python/python-REST-API-Http-Requests-for-Humans-with-Flask.php
#https://www.nintyzeros.com/2019/11/flask-mysql-crud-restful-api.html

import json
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

@app.route('/transactions', methods = ['GET'])
def index():
    get_transactions = Transaction.query.all()
    transaction_schema = TransactionSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    return make_response(jsonify({"transaction": transaction}))

#return results by user id
#will likely be disabled to prevent abuse
@app.route('/transactions/user/<string:user>', methods = ['GET'])
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
@app.route('/transactions/item/<string:item>', methods = ['GET'])
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
    
if __name__ == "__main__":
    app.run(debug=True)