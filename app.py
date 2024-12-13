from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:DSJ9tN8De8i3MnRGIwypnF1kwVKNZ2Yw@dpg-ct4a1nl2ng1s73a3t47g-a.frankfurt-postgres.render.com/project_2hrv'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)

class AlcoholProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    storage_duration = db.Column(db.Integer, nullable=False)

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('alcohol_product.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    storage_period = db.Column(db.Integer, nullable=False)
    investment_date = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/update_user', methods=['POST'])
def update_user():
    data = request.get_json()
    user = User.query.get(data['id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/add_alcohol', methods=['POST'])
def add_alcohol():
    data = request.get_json()
    new_product = AlcoholProduct(
        company_id=data['company_id'],
        name=data['name'],
        type=data['type'],
        storage_duration=data['storage_duration']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Alcohol product added successfully'})

@app.route('/delete_alcohol/<int:id>', methods=['DELETE'])
def delete_alcohol(id):
    product = AlcoholProduct.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/add_investment', methods=['POST'])
def add_investment():
    data = request.get_json()
    new_investment = Investment(
        client_id=data['client_id'],
        product_id=data['product_id'],
        amount=data['amount'],
        storage_period=data['storage_period']
    )
    db.session.add(new_investment)
    db.session.commit()
    return jsonify({'message': 'Investment saved successfully'})

@app.route('/investments/<int:client_id>', methods=['GET'])
def fetch_investments(client_id):
    investments = Investment.query.filter_by(client_id=client_id).all()
    result = [
        {
            'id': i.id,
            'product_name': AlcoholProduct.query.get(i.product_id).name,
            'amount': i.amount,
            'storage_period': i.storage_period,
            'investment_date': i.investment_date
        }
        for i in investments
    ]
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
