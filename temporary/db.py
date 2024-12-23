import os
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
import base64
from flask_cors import CORS

# Ініціалізація Flask
app = Flask(__name__)

# Дозволити CORS для всіх маршрутів
CORS(app)

# Підключення до бази даних SQL Server через Windows Authentication
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@localhost/TestDatabase?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ініціалізація SQLAlchemy
db = SQLAlchemy(app)

# Опис моделі таблиці Photos
class Photo(db.Model):
    __tablename__ = 'Photos'
    photo_id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String, nullable=False)

# API маршрут для отримання фото за його photo_id
@app.route('/api/photos/<int:photo_id>', methods=['GET'])
def get_photo(photo_id):
    # Знайти фото у базі даних
    photo = Photo.query.filter_by(photo_id=photo_id).first()
    if not photo:
        return jsonify({"error": "Photo not found"}), 404

    # Отримати абсолютний шлях до файлу
    abs_file_path = os.path.join(os.getcwd(), photo.file_path)

    # Перевірити, чи існує файл
    if not os.path.exists(abs_file_path):
        return jsonify({"error": "File not found on server"}), 404

    # Відкрити файл та закодувати в Base64
    with open(abs_file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # Повернути відповідь із закодованим зображенням
    return jsonify({"photo_id": photo.photo_id, "file_path": photo.file_path, "image_base64": encoded_string})

if __name__ == "__main__":
    app.run(debug=True)
