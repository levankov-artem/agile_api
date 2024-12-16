from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:DSJ9tN8De8i3MnRGIwypnF1kwVKNZ2Yw@dpg-ct4a1nl2ng1s73a3t47g-a.frankfurt-postgres.render.com/project_2hrv'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'qeV5c1nsqKZ7pNFt2EO0HPGgBADipaHH'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
Session(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "https://fantastic-melba-aad350.netlify.app"}})

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)

class AlcoholProduct(db.Model):
    __tablename__ = 'alcohol_production'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    storage_duration = db.Column(db.Integer, nullable=False)

class Investment(db.Model):
    __tablename__ = 'investments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('alcohol_product.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    storage_period = db.Column(db.Integer, nullable=False)

@app.route('/test_session', methods=['GET'])
def test_session():
    if 'user_id' in session:
        return jsonify({'message': 'Session is active', 'user_id': session['user_id']}), 200
    else:
        return jsonify({'error': 'No active session'}), 403

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')

    if not username or not email or not password or not user_type:
        return jsonify({'error': 'All fields are required'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password, user_type=user_type)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_type'] = user.user_type
        return jsonify({'message': 'Login successful', 'user_id': user.id, 'user_type': user.user_type}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/user/<int:id>', methods=['GET'])
def get_user_details(id):
    if 'user_id' not in session or session['user_id'] != id:
        return jsonify({'error': 'Unauthorized access'}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type
    })

@app.route('/update_user', methods=['POST'])
def update_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/investments', methods=['POST'])
def create_investment():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()

    try:
        client_id = int(data.get('client_id'))  # Ensure it's an integer
        product_id = int(data.get('product_id'))  # Ensure it's an integer
        amount = float(data.get('amount'))  # Ensure it's a float
        storage_period = int(data.get('storage_period'))  # Ensure it's an integer
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid input data'}), 400

    if not client_id or not product_id or not amount or not storage_period:
        return jsonify({'error': 'All fields are required'}), 400

    new_investment = Investment(
        client_id=client_id,
        product_id=product_id,
        amount=amount,
        storage_period=storage_period
    )

    try:
        db.session.add(new_investment)
        db.session.commit()
        return jsonify({'message': 'Investment created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/investments/<int:client_id>', methods=['GET'])
def get_investments(client_id):
    if 'user_id' not in session or session['user_id'] != client_id:
        return jsonify({'error': 'Unauthorized access'}), 403

    investments = Investment.query.filter_by(client_id=client_id).all()
    if not investments:
        return jsonify({'message': 'No investments found'}), 404

    investment_list = [{
        'id': inv.id,
        'product_id': inv.product_id,
        'amount': inv.amount,
        'storage_period': inv.storage_period,
        'investment_date': inv.investment_date
    } for inv in investments]

    return jsonify(investment_list), 200

@app.route('/investments/<int:investment_id>', methods=['DELETE'])
def delete_investment(investment_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 403

    investment = Investment.query.get(investment_id)
    if not investment or investment.client_id != session['user_id']:
        return jsonify({'error': 'Investment not found or unauthorized access'}), 404

    try:
        db.session.delete(investment)
        db.session.commit()
        return jsonify({'message': 'Investment deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/companies', methods=['GET'])
def get_companies():
    companies = User.query.filter_by(user_type='company').all()
    result = []
    for company in companies:
        products = AlcoholProduct.query.filter_by(company_id=company.id).all()
        product_list = [{'name': p.name, 'type': p.type, 'storage_duration': p.storage_duration} for p in products]
        result.append({'company_name': company.username, 'products': product_list})
    return jsonify(result), 200

@app.route('/products', methods=['POST'])
def register_product():

    data = request.get_json()
    name = data.get('name')
    type = data.get('type')
    storage_duration = data.get('storage_duration')

    if not name or not type or not storage_duration:
        return jsonify({'error': 'All fields are required'}), 400

    new_product = AlcoholProduct(
        company_id=session['user_id'],
        name=name,
        type=type,
        storage_duration=storage_duration
    )

    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product registered successfully'}), 201

@app.route('/investments_list', methods=['GET'])
def get_investments_list():
    if 'user_id' not in session or session['user_type'] != 'client':
        return jsonify({'error': 'Unauthorized access'}), 403

    investments = Investment.query.filter_by(client_id=session['user_id']).all()
    result = []
    for inv in investments:
        product = AlcoholProduct.query.get(inv.product_id)
        result.append({
            'id': inv.id,
            'product_name': product.name,
            'amount': inv.amount,
            'storage_period': inv.storage_period
        })
    return jsonify(result), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
