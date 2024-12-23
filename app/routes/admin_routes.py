from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Object, db
from sqlalchemy.exc import IntegrityError
from datetime import date
import os
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import Photo  # Модель для таблиці Photos

# Дозволені розширення файлів
ALLOWED_EXTENSIONS = {'png', 'jpg', 'bmp', 'HEIC'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/upload-photo/<int:object_id>', methods=['POST'])
@jwt_required()
def upload_photo(object_id):
    # Перевірка об'єкта
    obj = Object.query.get(object_id)
    if not obj:
        return jsonify({"error": "Object not found"}), 404

    # Перевірка наявності файлу у запиті
    if 'photo' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['photo']

    # Перевірка, чи файл завантажено
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Отримання папки для завантаження
    upload_folder = current_app.config['UPLOAD_FOLDER']
    object_folder = os.path.join("app", upload_folder)  # Шлях для збереження в app/upload

    # Генерація шляху для файлу
    file_path = os.path.join(object_folder, file.filename)

    # Збереження файлу
    file.save(file_path)

    # Відносний шлях для збереження у БД
    relative_path = f"app\\{os.path.relpath(file_path, current_app.root_path)}"


    # Додавання запису до бази даних
    photo = Photo(object_id=object_id, file_path=relative_path)
    db.session.add(photo)
    db.session.commit()

    return jsonify({"message": "Photo uploaded successfully", "file_path": relative_path}), 201


@admin_routes.route('/admin/add-object', methods=['POST'])
@jwt_required()
def add_object():
    data = request.json
    required_fields = [
        "title", "price", "square", "rooms", "total_floors", 
        "location", "category", "heating", "code", "type"
    ]
    
    # Перевірка обов'язкових полів
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Field {field} is required"}), 400

    # Додавання нового об'єкта
    try:
        new_object = Object(
            title=data["title"],
            description=data.get("description"),
            type=data["type"],
            rooms=int(data["rooms"]),
            floor=data.get("floor"),  # Може бути відсутнє
            total_floors=int(data["total_floors"]),
            location=data["location"],
            category=data["category"],
            heating=data["heating"],
            balcony=bool(data.get("balcony", False)),
            square=float(data["square"]),
            price=float(data["price"]),
            status="доступний",
            code=int(data["code"]),
            created_date=date.today()  # Автоматично встановлюємо сьогоднішню дату
        )
        db.session.add(new_object)
        db.session.commit()
        return jsonify({"message": "Object added successfully"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Object with this code already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Маршрут для зміни статусу об'єкта
@admin_routes.route('/admin/change-status/<int:object_id>', methods=['PATCH'])
@jwt_required()
def change_status(object_id):
    try:
        obj = Object.query.get(object_id)
        if not obj:
            return jsonify({"error": "Object not found"}), 404
        if obj.status == "проданий":
            return jsonify({"message": "Object is already sold"}), 400

        obj.status = "проданий"
        db.session.commit()
        return jsonify({"message": f"Object {obj.object_id} status changed to 'проданий'"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
