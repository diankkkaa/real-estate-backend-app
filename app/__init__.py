import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import Config

# Ініціалізація розширень
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    # Налаштування каталогу для зберігання фотографій
    app.config['UPLOAD_FOLDER'] = 'upload'

    # Ініціалізація розширень
    db.init_app(app)
    jwt.init_app(app)

    # Реєстрація маршрутів
    from .routes import auth_routes, protected, object_routes, admin_routes
    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(protected.protected_bp)
    app.register_blueprint(object_routes.bp)
    app.register_blueprint(admin_routes.admin_routes)

    return app
