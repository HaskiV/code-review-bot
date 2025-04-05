from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .service import AuthService
# from backend.api.routes import api as api_bp

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint для входа в систему"""
    if not request.is_json:
        return jsonify({"error": "Ожидается JSON"}), 400
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Необходимо указать имя пользователя и пароль"}), 400
    
    success, user = auth_service.authenticate(username, password)
    
    if not success:
        return jsonify({"error": "Неверное имя пользователя или пароль"}), 401
    
    try:
        access_token = auth_service.create_access_token(username)
        
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user["id"],
                "role": user["role"]
            }
        })
    except Exception as e:
        return jsonify({"error": f"Ошибка при создании токена: {str(e)}"}), 500

@auth_bp.route('/api-keys', methods=['GET'])
@jwt_required()
def get_api_keys():
    """Endpoint для получения API ключей пользователя"""
    user_id = get_jwt_identity()
    
    if user_id not in auth_service.users:
        return jsonify({"error": "Пользователь не найден"}), 404
    
    user = auth_service.users[user_id]
    api_keys = user.get("api_keys", {})
    
    return jsonify({"api_keys": api_keys})

@auth_bp.route('/api-keys', methods=['POST'])
@jwt_required()
def create_api_key():
    """Endpoint для создания нового API ключа"""
    user_id = get_jwt_identity()
    
    if user_id not in auth_service.users:
        return jsonify({"error": "Пользователь не найден"}), 404
    
    if not request.is_json:
        return jsonify({"error": "Ожидается JSON"}), 400
    
    data = request.json
    key_name = data.get('name')
    
    if not key_name:
        return jsonify({"error": "Необходимо указать имя ключа"}), 400
    
    # Валидация имени ключа
    if not isinstance(key_name, str) or len(key_name) < 3 or len(key_name) > 50:
        return jsonify({"error": "Имя ключа должно быть строкой длиной от 3 до 50 символов"}), 400
    
    # Проверка на допустимые символы
    if not all(c.isalnum() or c in '-_' for c in key_name):
        return jsonify({"error": "Имя ключа может содержать только буквы, цифры, дефис и подчеркивание"}), 400
    
    user = auth_service.users[user_id]
    
    if "api_keys" not in user:
        user["api_keys"] = {}
    
    # Ограничение на количество ключей
    max_keys = 5  # Максимальное количество ключей для одного пользователя
    if len(user["api_keys"]) >= max_keys:
        return jsonify({"error": f"Достигнуто максимальное количество API ключей ({max_keys})"}), 400
    
    if key_name in user["api_keys"]:
        return jsonify({"error": f"Ключ с именем '{key_name}' уже существует"}), 400
    
    api_key = auth_service._generate_api_key()
    user["api_keys"][key_name] = api_key
    
    auth_service.save_users()
    
    return jsonify({
        "name": key_name,
        "key": api_key
    })

@auth_bp.route('/api-keys/<key_name>', methods=['DELETE'])
@jwt_required()
def delete_api_key(key_name):
    """Endpoint для удаления API ключа"""
    user_id = get_jwt_identity()
    
    if user_id not in auth_service.users:
        return jsonify({"error": "Пользователь не найден"}), 404
    
    user = auth_service.users[user_id]
    
    if "api_keys" not in user or key_name not in user["api_keys"]:
        return jsonify({"error": f"Ключ с именем '{key_name}' не найден"}), 404
    
    # Проверка, что у пользователя останется хотя бы один ключ
    if len(user["api_keys"]) <= 1:
        return jsonify({"error": "Невозможно удалить последний API ключ"}), 400
    
    del user["api_keys"][key_name]
    
    auth_service.save_users()
    
    return jsonify({"message": f"Ключ '{key_name}' успешно удален"})