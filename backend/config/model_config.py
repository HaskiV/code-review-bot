"""
Конфигурация ML моделей, используемых для анализа кода.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from backend.config.env import get_env_variable, BASE_DIR

# Пути для конфигурации моделей
CONFIG_DIR = Path(__file__).resolve().parent
MODELS_CONFIG_FILE = CONFIG_DIR / "models_config.json"
PROMPTS_CONFIG_FILE = CONFIG_DIR / "prompts_config.json"

# Настройки кэша по умолчанию
DEFAULT_CACHE_SETTINGS = {
    "enabled": True,
    "cache_dir": str(BASE_DIR / "cache"),
    "expiry_time": 3600  # 1 час в секундах
}

def get_model_parameters(provider: str, model_name: str = None) -> Optional[Dict[str, Any]]:
    """Получение параметров для конкретной модели."""
    # Параметры по умолчанию для каждого провайдера
    defaults = {
        "openai": {"temperature": 0.3, "max_tokens": 1000, "top_p": 1.0},
        "anthropic": {"temperature": 0.3, "max_tokens": 1000},
        "huggingface": {"temperature": 0.7, "max_length": 1000, "top_p": 0.9}
    }
    return defaults.get(provider, {})

def get_prompt_template(provider: str) -> Dict[str, str]:
    """Получение шаблона запроса для конкретного провайдера."""
    default_template = """Проанализируйте следующий код на {language} и предложите улучшения:

```{language}
{code}
Пожалуйста, предоставьте:

1. Проблемы качества кода
2. Потенциальные ошибки
3. Улучшения производительности
4. Проблемы безопасности
5. Рекомендации по лучшим практикам"""
   
    return {"user_message": default_template}
def get_response_parsing_config(provider: str) -> Dict[str, Any]:
    """Получение конфигурации для разбора ответов модели."""
    return {
        "format": "markdown",
        "sections": ["Качество кода", "Ошибки", "Производительность", "Безопасность", "Лучшие практики"]
    }

### 1. Обновление конфигурации моделей

def get_model_config(model_id: str) -> Optional[dict]:
    """
    Получение конфигурации модели по идентификатору.
    
    Args:
        model_id: Идентификатор модели
        
    Returns:
        Конфигурация модели или None, если модель не найдена
    """
    # Ищем модель в доступных моделях
    for provider, models in AVAILABLE_MODELS.items():
        if model_id in models:
            config = models[model_id].copy()
            # Сохраняем оригинальный тип, если он указан
            if "type" not in config:
                config["type"] = provider
            return config
    
    # Проверяем локальные модели
    if model_id in LOCAL_MODELS:
        return LOCAL_MODELS[model_id].copy()
    
    return None

def is_caching_enabled() -> bool:
    """Проверка, включено ли кэширование."""
    return get_env_variable("ENABLE_CACHE", "True").lower() in ("true", "1", "yes")

def get_cache_settings() -> Dict[str, Any]:
    """Получение настроек кэша."""
    settings = DEFAULT_CACHE_SETTINGS.copy()
    return settings

# Добавьте конфигурацию доступных моделей
# Добавьте в AVAILABLE_MODELS
AVAILABLE_MODELS = {
    "openai": {
        "gpt-4o": {
            "name": "gpt-4o",
            "description": "Самая продвинутая модель OpenAI, лучшая для сложного анализа кода",
            "max_tokens": 4096,
            "is_default": False
        },
        "gpt-4o-mini": {
            "name": "gpt-4o mini",
            "description": "Меньшая и более быстрая версия GPT-4o",
            "max_tokens": 4096,
            "is_default": False
        }
    },
    "proxy": {
        "gpt-4o-proxy": {
            "name": "GPT-4o Proxy",
            "description": "GPT-4o через прокси-сервер",
            "max_tokens": 4096,
            "is_default": False,
            "base_url": "https://api.sree.shop/v1",
            "actual_model": "gpt-4o"
        },
        "deepseek-v3": {
            "name": "DeepSeek Coder V3",
            "description": "DeepSeek Coder V3 через OpenRouter",
            "max_tokens": 4096,
            "is_default": False,
            "base_url": "https://openrouter.ai/api/v1",
            "actual_model": "deepseek/deepseek-v3-base:free"
        }
    },
    "mock": {
        "mock-model": {
            "name": "Mock Model",
            "description": "Для тестирования без реальных API-вызовов",
            "is_default": False,
            "type": "mock"
        }
    },
    "gradio": {
        "claude-3-7": {
            "name": "Claude 3.7",
            "description": "Claude 3.7 через Gradio API",
            "api_url": "hysts-samples/claude-3-7-sample",  # Проверьте этот URL
            "max_tokens": 8000,
            "is_default": True,
            "type": "gradio"
        }
    }
}

# Добавьте в существующий файл

from pathlib import Path
from backend.config.env import BASE_DIR

# Конфигурация локальных моделей
LOCAL_MODELS = {
    "mistral-7b": {
        "name": "Mistral 7B",
        "path": "models/mistral-7b-instruct-v0.2",
        "type": "local",  # Изменено с "mistral" на "local"
        "description": "Mistral 7B Instruct - легковесная модель для анализа кода",
        "quantization": "4bit",
        "is_default": False
    },
    "llama-2-7b": {
        "name": "Llama 2 7B",
        "path": "models/llama-2-7b-chat",
        "type": "llama",
        "description": "Meta Llama 2 7B Chat - модель для анализа кода",
        "quantization": "4bit",
        "is_default": False
    },
    "codellama-7b": {
        "name": "CodeLlama 7B",
        "path": "models/codellama-7b-instruct",
        "type": "llama",
        "description": "CodeLlama 7B - специализированная модель для анализа кода",
        "quantization": "4bit",
        "is_default": False
    }
}

# Добавьте переменную для токена Hugging Face
HUGGINGFACE_TOKEN = get_env_variable("HUGGINGFACE_TOKEN", "")

def get_local_model_path(model_id):
    """Получение пути к локальной модели."""
    model_config = LOCAL_MODELS.get(model_id)
    if not model_config:
        return None
    
    # Проверяем, является ли путь абсолютным
    path = model_config["path"]
    if os.path.isabs(path):
        return path
    
    # Если путь относительный, добавляем BASE_DIR
    return str(Path(BASE_DIR) / path)

# Добавьте эту функцию в файл model_config.py после определения LOCAL_MODELS

def get_local_model_config(model_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Получение конфигурации локальной модели по имени.
    
    Args:
        model_name: Имя модели (если None, возвращается конфигурация модели по умолчанию)
        
    Returns:
        Конфигурация модели или None, если модель не найдена
    """
    # Если имя модели не указано, используем модель по умолчанию
    if model_name is None:
        # Находим модель, помеченную как is_default=True
        for model_id, config in LOCAL_MODELS.items():
            if config.get("is_default", False):
                return config.copy()
        # Если нет модели по умолчанию, используем первую модель из списка
        if LOCAL_MODELS:
            first_model = next(iter(LOCAL_MODELS.values()))
            return first_model.copy()
        return None
    
    # Если имя модели указано, ищем её в списке локальных моделей
    if model_name in LOCAL_MODELS:
        return LOCAL_MODELS[model_name].copy()
    
    return None