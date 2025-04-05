"""
Конфигурация окружения для Code Review Bot.
Загружает переменные окружения из файла .env и предоставляет функции для работы с ними.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
# Добавьте импорт для загрузки .env файла, если его еще нет
from dotenv import load_dotenv
load_dotenv()

# Убедитесь, что есть функция для получения OPENAI_API_KEY
def get_openai_api_key():
    return get_env_variable("OPENAI_API_KEY", "")

def get_proxy_api_key():
    """Получение API ключа для прокси-сервера"""
    return get_env_variable("API_KEY", "")

# Определение базовых путей
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env'
CONFIG_DIR = BASE_DIR / 'config'
SECRETS_FILE = CONFIG_DIR / 'secrets.json'

# Значения по умолчанию для критических переменных
DEFAULT_VALUES = {
    "ENVIRONMENT": "development",
    "DEBUG_MODE": "False",
    "PORT": "5000",
    "HOST": "0.0.0.0",
    "LOG_LEVEL": "INFO",
    "MAX_CODE_LENGTH": "10000",
    "REQUEST_TIMEOUT": "60",
    "CACHE_EXPIRY": "3600"
}

# Загрузка переменных окружения из файла .env, если он существует
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    print(f"Файл .env не найден по пути {ENV_FILE}. Используются значения по умолчанию.")

def get_env_variable(name: str, default: Any = None) -> Any:
    """
    Получение переменной окружения или возврат значения по умолчанию
    
    Args:
        name: Имя переменной окружения
        default: Значение по умолчанию, если переменная окружения не установлена
        
    Returns:
        Значение переменной окружения или значение по умолчанию
    """
    # Сначала проверяем переменные окружения
    value = os.environ.get(name)
    
    # Если не найдено, проверяем DEFAULT_VALUES
    if value is None and name in DEFAULT_VALUES:
        value = DEFAULT_VALUES[name]
    
    # Если всё ещё не найдено, используем переданное значение по умолчанию
    if value is None:
        value = default
        
    return value

def get_api_key(service_name: str) -> Optional[str]:
    """
    Получение API ключа для указанного сервиса из переменных окружения или файла secrets.json
    
    Args:
        service_name: Название сервиса (openai, anthropic, huggingface и т.д.)
    
    Returns:
        API ключ или None, если ключ не найден
    """
    # Сначала проверяем переменные окружения
    env_var_name = f"{service_name.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    
    if api_key:
        return api_key
    
    # Если ключ не найден в переменных окружения, проверяем файл secrets.json
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r") as f:
                secrets = json.load(f)
                # Проверяем структуру с api_keys
                if "api_keys" in secrets and service_name in secrets["api_keys"]:
                    return secrets["api_keys"][service_name]
        except Exception as e:
            print(f"Ошибка при чтении файла secrets.json: {str(e)}")
    
    return None

def is_production() -> bool:
    """Проверка, работает ли приложение в производственном режиме"""
    return get_env_variable("ENVIRONMENT", "development").lower() == "production"

def is_development() -> bool:
    """Проверка, работает ли приложение в режиме разработки"""
    return get_env_variable("ENVIRONMENT", "development").lower() == "development"

def is_testing() -> bool:
    """Проверка, работает ли приложение в режиме тестирования"""
    return get_env_variable("ENVIRONMENT", "development").lower() == "testing"

def is_debug_mode() -> bool:
    """Проверка, включен ли режим отладки"""
    return get_env_variable("DEBUG_MODE", "False").lower() in ("true", "1", "yes")

def get_port() -> int:
    """Получение порта для запуска приложения"""
    return int(get_env_variable("PORT", 5000))

def get_host() -> str:
    """Получение хоста для запуска приложения"""
    return get_env_variable("HOST", "0.0.0.0")

def get_log_level() -> str:
    """Получение уровня логирования"""
    return get_env_variable("LOG_LEVEL", "INFO").upper()

def get_request_timeout() -> int:
    """Получение таймаута для запросов в секундах"""
    return int(get_env_variable("REQUEST_TIMEOUT", 60))

def get_max_code_length() -> int:
    """Получение максимальной длины кода для анализа"""
    return int(get_env_variable("MAX_CODE_LENGTH", 100000))

def save_api_key(provider: str, api_key: str) -> bool:
    """
    Сохранение API ключа в файл secrets.json
    
    Args:
        provider: Имя провайдера (openai, anthropic, huggingface)
        api_key: API ключ
        
    Returns:
        True, если сохранение успешно, иначе False
    """
    # Создаем директорию config, если она не существует
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Имя переменной окружения для API ключа
    env_var_name = f"{provider.upper()}_API_KEY"
    
    # Загружаем существующие секреты или создаем новый словарь
    secrets: Dict[str, str] = {}
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, 'r') as f:
                secrets = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # Добавляем или обновляем API ключ
    secrets[env_var_name] = api_key
    
    # Сохраняем секреты в файл
    try:
        with open(SECRETS_FILE, 'w') as f:
            json.dump(secrets, f, indent=4)
        return True
    except Exception:
        return False

def create_env_file_if_not_exists() -> bool:
    """
    Создает файл .env с значениями по умолчанию, если он не существует
    
    Returns:
        True, если файл создан или уже существует, иначе False
    """
    if ENV_FILE.exists():
        return True
        
    try:
        with open(ENV_FILE, 'w') as f:
            for key, value in DEFAULT_VALUES.items():
                f.write(f"{key}={value}\n")
            
            # Добавляем пустые значения для API ключей
            f.write("OPENAI_API_KEY=\n")
            f.write("ANTHROPIC_API_KEY=\n")
            f.write("HUGGINGFACE_API_KEY=\n")
            
        return True
    except Exception:
        return False

# Создаем файл .env при импорте модуля, если он не существует
create_env_file_if_not_exists()

# Добавьте в файл env.py функцию для хранения API ключей
API_KEYS = {
    "openai": get_env_variable("OPENAI_API_KEY", ""),
    "proxy": get_env_variable("PROXY_API_KEY", ""),  # Добавьте эту строку для прокси-API ключа
    "anthropic": get_env_variable("ANTHROPIC_API_KEY", ""),
    "huggingface": get_env_variable("HUGGINGFACE_API_KEY", "")
}

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider."""
    return API_KEYS.get(provider, "")