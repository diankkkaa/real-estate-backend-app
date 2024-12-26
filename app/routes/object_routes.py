from flask import Blueprint, jsonify, request
from sqlalchemy import desc, asc
from app.models import Object, Photo
from app import db
import os
import base64

bp = Blueprint('objects', __name__, url_prefix='/api')

# Функція для перетворення шляху до зображення в Base64
def encode_image_to_base64(file_path):
    abs_file_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(abs_file_path):
        return None
    with open(abs_file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@bp.route('/objects', methods=['POST'])
def get_filtered_objects():
    try:
        filters = request.json
        page = filters.get('page', 1)
        limit = filters.get('limit', 5)
        sort = filters.get('sort', 'newest')

        floor_min = filters.get('floor_min')
        floor_max = filters.get('floor_max')
        square_min = filters.get('square_min')
        square_max = filters.get('square_max')
        price_min = filters.get('price_min')
        price_max = filters.get('price_max')
        rooms_min = filters.get('rooms_min')
        rooms_max = filters.get('rooms_max')

        rooms_type = filters.get('rooms_type')
        category_filter = filters.get('category')
        type_filter = filters.get('type')

        if sort == 'newest':
            order_by = desc(Object.created_date)
        elif sort == 'oldest':
            order_by = asc(Object.created_date)
        elif sort == 'cheapest':
            order_by = asc(Object.price)
        elif sort == 'expensive':
            order_by = desc(Object.price)
        else:
            return jsonify({"error": "Invalid sort parameter"}), 400

        query = Object.query.filter(Object.status == 'доступний')

        def validate_and_filter(query, param_min, param_max, column, name):
            if param_min is not None:
                try:
                    param_min = float(param_min)
                except ValueError:
                    raise ValueError(f"{name}_min must be a valid number")
                query = query.filter(column >= param_min)
            if param_max is not None:
                try:
                    param_max = float(param_max)
                except ValueError:
                    raise ValueError(f"{name}_max must be a valid number")
                query = query.filter(column <= param_max)
            if param_min is not None and param_max is not None and param_min > param_max:
                raise ValueError(f"{name}_min cannot be greater than {name}_max")
            return query

        query = validate_and_filter(query, floor_min, floor_max, Object.floor, "floor")
        query = validate_and_filter(query, square_min, square_max, Object.square, "square")
        query = validate_and_filter(query, price_min, price_max, Object.price, "price")
        query = validate_and_filter(query, rooms_min, rooms_max, Object.rooms, "rooms")

        if rooms_type == "1":
            query = query.filter(Object.rooms == 1)
        elif rooms_type == "2":
            query = query.filter(Object.rooms == 2)
        elif rooms_type == "3":
            query = query.filter(Object.rooms == 3)
        elif rooms_type == "4+":
            query = query.filter(Object.rooms >= 4)

        if category_filter:
            query = query.filter(Object.category == category_filter)

        if type_filter:
            query = query.filter(Object.type == type_filter)

        offset = (page - 1) * limit
        objects_query = query.order_by(order_by).offset(offset).limit(limit).all()

        objects = []
        for obj in objects_query:
            photos = []
            for photo in obj.photos:
                encoded_photo = encode_image_to_base64(photo.file_path)
                if encoded_photo:
                    photos.append({"photo_id": photo.photo_id, "image_base64": encoded_photo})

            objects.append({
                "id": obj.object_id,
                "title": obj.title,
                "price": float(obj.price),
                "square": float(obj.square),
                "rooms": obj.rooms,
                "floor": obj.floor,
                "location": obj.location,
                "price_per_sq_meter": obj.price_per_sq_meter,
                "created_date": obj.created_date.strftime('%Y-%m-%d'),
                "photos": [
            {
                "photo_id": photo.photo_id,
                "image_base64": base64.b64encode(open(photo.file_path, "rb").read()).decode("utf-8")
            }
            for photo in obj.photos
        ]
            })

        total_objects = query.count()
        total_pages = (total_objects + limit - 1) // limit

        return jsonify({
            "objects": objects,
            "total_objects": total_objects,
            "total_pages": total_pages,
            "current_page": page
        })

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/objects/<int:object_id>', methods=['GET'])
def get_object_details(object_id):
    obj = Object.query.filter_by(object_id=object_id).first()

    if not obj:
        return jsonify({"error": "Object not found"}), 404

    photos = []
    for photo in obj.photos:
        encoded_photo = encode_image_to_base64(photo.file_path)
        if encoded_photo:
            photos.append({"photo_id": photo.photo_id, "image_base64": encoded_photo})

    object_details = {
        "id": obj.object_id,
        "title": obj.title,
        "description": obj.description,
        "type": obj.type,
        "rooms": obj.rooms,
        "floor": obj.floor,
        "total_floors": obj.total_floors,
        "location": obj.location,
        "category": obj.category,
        "heating": obj.heating,
        "balcony": obj.balcony,
        "square": float(obj.square),
        "price": float(obj.price),
        "status": obj.status,
        "code": obj.code,
        "created_date": obj.created_date.strftime('%Y-%m-%d'),
        "price_per_sq_meter": obj.price_per_sq_meter,
        "photos": photos
    }

    return jsonify(object_details)


@bp.route('/objects/favorites', methods=['POST'])
def get_short_info():
    try:
        # Отримуємо масив ID об'єктів із запиту
        object_ids = request.json.get('object_ids', [])
        
        # Перевіряємо, чи масив ID є валідним
        if not isinstance(object_ids, list) or not all(isinstance(id, int) for id in object_ids):
            return jsonify({"error": "Invalid object_ids. It should be a list of integers."}), 400
        
        # Отримуємо об'єкти з бази даних за ID
        objects_query = Object.query.filter(Object.object_id.in_(object_ids)).all()

        # Формуємо відповідь із частковою інформацією
        objects = []
        for obj in objects_query:
            # Отримуємо перше фото, якщо є
            first_photo = obj.photos[0] if obj.photos else None
            encoded_photo = encode_image_to_base64(first_photo.file_path) if first_photo else None
            
            # Додаємо об'єкт у список
            objects.append({
                "id": obj.object_id,
                "title": obj.title,
                "price": float(obj.price),
                "square": float(obj.square),
                "rooms": obj.rooms,
                "floor": obj.floor,
                "location": obj.location,
                "price_per_sq_meter": obj.price_per_sq_meter,
                "created_date": obj.created_date.strftime('%Y-%m-%d'),
                "photo": encoded_photo  # Одне фото або None
            })

        return jsonify({"objects": objects}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
