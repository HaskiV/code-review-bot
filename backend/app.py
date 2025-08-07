from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.api.routes import api
from backend.auth.routes import auth_bp
from backend.config.env import get_env_variable, get_host, get_port, is_debug_mode, get_request_timeout, get_max_code_length, get_redis_url
# Импортируем команды
from backend.commands import download_model_command, load_models_command

def create_app():
    """Создание и настройка Flask-приложения."""
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    # Настройка приложения из переменных окружения
    app.config["SECRET_KEY"] = get_env_variable("SECRET_KEY", "default-secret-key-change-in-production")
    app.config["DEBUG"] = is_debug_mode()
    app.config["MAX_CONTENT_LENGTH"] = get_env_variable("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)  # 16 MB
    app.config["MAX_CODE_LENGTH"] = get_max_code_length()
    app.config["RATE_LIMIT_PER_MINUTE"] = int(get_env_variable("RATE_LIMIT_PER_MINUTE", 60))
    app.config["REQUEST_TIMEOUT"] = get_request_timeout()
    
    # Настройка JWT
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(get_env_variable("JWT_ACCESS_TOKEN_EXPIRES", 86400))  # 24 часа
    jwt = JWTManager(app)
    
    # Настройка ограничителя скорости
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[f"{app.config['RATE_LIMIT_PER_MINUTE']} per minute"],
        storage_uri=get_redis_url()
    )
    
    # Регистрация Blueprint
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Регистрация команд Flask CLI
    app.cli.add_command(download_model_command)
    app.cli.add_command(load_models_command)
    
    # Обработчик ошибок 404
    @app.errorhandler(404)
    def page_not_found(e):
        return app.send_static_file('index.html')
    
    # Обработчик ошибок 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500
    
    # Асинхронная предварительная загрузка моделей
    from backend.api.routes import model_service
    model_service.preload_models_in_background()
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=get_host(), port=get_port(), debug=is_debug_mode())