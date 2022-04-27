from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://owls:vHAxYRzjZYSEr6E@owls-db.c9hvuhvpnktp.us-west-2.rds.amazonaws.com/owls'
db = SQLAlchemy(app)

###Models####
class Owls(db.Model):
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
class OwlsSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Owls
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
    get_transactions = Owls.query.all()
    transaction_schema = OwlsSchema(many=True)
    transaction = transaction_schema.dump(get_transactions)
    return make_response(jsonify({"transaction": transaction}))
#@app.route('/transactions/<id>', methods = ['GET'])
#def get_product_by_id(ds):
    #get_transactions = Owls.query.get(ds)
    #transaction_schema = OwlsSchema()
    #transactions = transaction_schema.dump(get_transactions)
    #return make_response(jsonify({"transaction": transactions}))
#@app.route('/transactions/<id>', methods = ['PUT'])
#def update_product_by_id(id):
    #data = request.get_json()
    #get_product = Owls.query.get(id)
    #if data.get('title'):
        #get_product.title = data['title']
    #if data.get('productDescription'):
        #get_product.productDescription = data['productDescription']
    #if data.get('productBrand'):
        #get_product.productBrand = data['productBrand']
    #if data.get('price'):
        #get_product.price= data['price']    
    #db.session.add(get_product)
    #db.session.commit()
    #product_schema = OwlsSchema(only=['id', 'title', 'productDescription','productBrand','price'])
    #product = product_schema.dump(get_product)
    #return make_response(jsonify({"product": product}))
#@app.route('/products/<id>', methods = ['DELETE'])
#def delete_product_by_id(id):
    #get_product = Owls.query.get(id)
    #db.session.delete(get_product)
    #db.session.commit()
    #return make_response("",204)
#@app.route('/products', methods = ['POST'])
#def create_product():
    #data = request.get_json()
    #product_schema = OwlsSchema()
    #product = product_schema.load(data)
    #result = product_schema.dump(product.create())
    #return make_response(jsonify({"product": result}),200)
if __name__ == "__main__":
    app.run(debug=True)