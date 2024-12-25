from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Object, Photo, db
from sqlalchemy.exc import IntegrityError
from datetime import date
import os
from flask import current_app
from werkzeug.utils import secure_filename

# Дозволені розширення файлів
ALLOWED_EXTENSIONS = {'png', 'jpg', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/add-object-with-photos', methods=['POST'])
@jwt_required()
def add_object_with_photos():
    # Перевірка наявності файлів у запиті
    if 'photos' not in request.files:
        return jsonify({"error": "No photos in the request"}), 400

    files = request.files.getlist('photos')  # Отримуємо всі файли
    if not files or all(file.filename == '' for file in files):
        return jsonify({"error": "No files selected"}), 400

    # Перевірка обов'язкових текстових полів
    required_fields = [
        "title", "price", "square", "rooms", "total_floors", 
        "location", "category", "heating", "code", "type"
    ]
    data = request.form
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
        db.session.flush()  # Отримуємо object_id для фото

        # Завантаження кожного фото
        uploaded_photos = []
        upload_folder = current_app.config['UPLOAD_FOLDER']
        object_folder = os.path.join("app", upload_folder)  # Шлях для збереження в app/upload
        os.makedirs(object_folder, exist_ok=True)  # Створюємо папку, якщо її немає

        for file in files:
            if allowed_file(file.filename):
                # Генерація безпечного шляху для файлу
                filename = secure_filename(file.filename)
                file_path = os.path.join(object_folder, filename)
                file.save(file_path)

                # Відносний шлях для збереження у БД
                relative_path = f"app\\{os.path.relpath(file_path, current_app.root_path)}"

                # Додавання запису до бази даних
                photo = Photo(object_id=new_object.object_id, file_path=relative_path)
                db.session.add(photo)
                db.session.flush()  # Оновлюємо ID фото
                uploaded_photos.append(photo.photo_id)
            else:
                return jsonify({"error": f"Invalid file format for {file.filename}"}), 400

        db.session.commit()
        return jsonify({
            "message": "Object and photos added successfully",
            "object_id": new_object.object_id,
            "photo_ids": uploaded_photos  # Повертаємо всі ID завантажених фото
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Object with this code already exists"}), 400
    except Exception as e:
        db.session.rollback()
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
