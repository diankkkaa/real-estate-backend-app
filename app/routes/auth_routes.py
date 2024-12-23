from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from ..models import Administrator
from .. import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Перевірка, чи існує користувач
    existing_user = Administrator.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    # Хешування пароля
    hashed_password = generate_password_hash(password)
    new_admin = Administrator(email=email, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Перевірка, чи передано email і пароль
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Знайти користувача у БД
    user = Administrator.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Створити JWT токен
    auth_token = create_access_token(identity=str(user.administrator_id))
    return jsonify({"auth_token": auth_token}), 200
