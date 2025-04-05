from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import timedelta
from marshmallow import ValidationError
# from backend.core.static_analysis.analyzer import run_static_analysis
from backend.services.model_service import ModelService
from backend.schemas.validation import CodeReviewSchema, ModelSchema, ModelUpdateSchema
from backend.auth.service import AuthService
from backend.config.env import get_max_code_length

# Затем создаем экземпляры Blueprint и сервисов
api = Blueprint('api', __name__)
auth_bp = Blueprint('auth', __name__)
model_service = ModelService()
auth_service = AuthService()

# Инициализация схем валидации
code_review_schema = CodeReviewSchema()
model_schema = ModelSchema()
model_update_schema = ModelUpdateSchema()

@api.route('/review', methods=['POST'])
@api.route('/api/review', methods=['POST'])
def review_code():
    """Анализ кода с использованием выбранной модели."""
    from backend.services import model_service
    
    try:
        # Проверка JSON
        print(f"Заголовки запроса: {dict(request.headers)}")
        print(f"Тип содержимого запроса: {request.content_type}")
        print(f"Данные запроса: {request.data}")
        
        if not request.is_json:
            print("Запрос не в формате JSON")
            return jsonify({"success": False, "error": "Ожидается JSON"}), 400
            
        data = request.get_json()
        print(f"Полученные данные: {data}")
        
        if not data:
            return jsonify({"success": False, "error": "Отсутствуют данные запроса"}), 400
            
        # Валидация входных данных
        try:
            # Используем схему для валидации
            print(f"Валидация данных схемой: {data}")
            # Временно обходим валидацию схемы для отладки
            # validated_data = code_review_schema.load(data)
            validated_data = data
            code = validated_data.get('code', '')
            language = validated_data.get('language', '')
            model_id = validated_data.get('model_id') or data.get('model')
            
            # Проверяем наличие обязательных полей
            if not code:
                return jsonify({"success": False, "error": "Отсутствует код для анализа"}), 400
            if not language:
                return jsonify({"success": False, "error": "Отсутствует язык программирования"}), 400
            if not model_id:
                model_id = model_service.get_default_model()
                
            print(f"Валидация успешна: код={len(code)}, язык={language}, модель={model_id}")
        except ValidationError as err:
            print(f"Ошибка валидации: {err.messages}")
            return jsonify({"success": False, "error": "Ошибка валидации", "details": err.messages}), 400
        
        # Проверка размера кода
        max_code_length = get_max_code_length()
        if len(code) > max_code_length:
            return jsonify({
                "success": False, 
                "error": f"Размер кода превышает допустимый лимит ({max_code_length} символов)"
            }), 413
            
        # Получаем код, язык программирования и модель
        code = validated_data['code']
        language = validated_data['language']
        model_id = validated_data.get('model_id') or data.get('model')
        
        # Получаем предпочтительный язык ответа
        response_language = data.get('response_language', 'russian')
        
        # Анализ кода с использованием выбранной модели
        try:
            # Передаем параметр языка ответа
            result = model_service.analyze_code(
                code, 
                language, 
                model_id=model_id,
                response_language=response_language
            )
            
            # Убедимся, что результат - это строка
            if not isinstance(result, str):
                if isinstance(result, dict) or isinstance(result, list):
                    import json
                    result = json.dumps(result, ensure_ascii=False)
                else:
                    result = str(result)
            
            return jsonify({"success": True, "result": result})
        except Exception as model_error:
            print(f"Ошибка в анализе модели: {str(model_error)}")
            # Используем заглушку в случае ошибки модели
            result = model_service._get_mock_analysis(code, language)
            return jsonify({
                "success": True, 
                "result": result,
                "warning": f"Произошла ошибка при анализе модели, используется заглушка: {str(model_error)}"
            })
    except Exception as e:
        print(f"Ошибка в review_code: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Произошла ошибка при анализе кода: {str(e)}"
        }), 500
        
@auth_bp.route('/login', methods=['POST'])
def login():
    """Эндпоинт для входа в систему."""
    try:
        if not request.is_json:
            return jsonify({"error": "Ожидается JSON"}), 400

        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Требуется имя пользователя и пароль"}), 400
            
        success, user = auth_service.authenticate(username, password)
        
        if success:
            # Создаем JWT токен
            expires = timedelta(days=1)
            access_token = create_access_token(
                identity={"username": user.username, "role": user.role},
                expires_delta=expires
            )
            
            return jsonify({
                "message": "Вход выполнен успешно",
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "api_key": user.api_key
                }
            })
        else:
            return jsonify({"error": user}), 401
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Получение профиля пользователя."""
    try:
        current_user = get_jwt_identity()
        username = current_user.get('username')
        
        user = auth_service.users.get(username)
        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404
        
        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        })
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500


@api.route('/models', methods=['GET'])
def get_models():
    """Получение списка доступных моделей."""
    from backend.services import model_service
    
    try:
        # Получаем список доступных моделей
        models = model_service.get_models()
        default_model = model_service.get_default_model()
        
        print(f"Доступные модели: {models}")
        print(f"Модель по умолчанию: {default_model}")
        
        return jsonify({
            "success": True,
            "models": models,
            "default_model": default_model
        })
    except Exception as e:
        print(f"Ошибка при получении моделей: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Произошла ошибка при получении списка моделей: {str(e)}"
        }), 500