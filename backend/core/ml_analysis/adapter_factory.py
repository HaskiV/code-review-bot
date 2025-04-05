"""
Фабрика для создания адаптеров моделей.
"""
from typing import Dict, Any, Optional

# Импортируем новый адаптер
from backend.core.ml_analysis.openai_adapter import OpenAIAdapter
# Исправляем импорт - используем proxy_adapter вместо proxy_openai_adapter
from backend.core.ml_analysis.proxy_adapter import ProxyOpenAIAdapter
from backend.core.ml_analysis.mock_adapter import MockAdapter
from backend.config.model_config import get_model_config

# Базовый класс для адаптеров
class BaseModelAdapter:
    """Базовый класс для адаптеров моделей."""
    pass

def create_adapter(adapter_type: str, **kwargs) -> BaseModelAdapter:
    """
    Создание адаптера для модели.
    
    Args:
        adapter_type: Тип адаптера (openai, anthropic, mock и т.д.)
        **kwargs: Дополнительные параметры
        
    Returns:
        Адаптер для модели
    """
    model_id = kwargs.get("model_id", "")
    
    # Проверяем, является ли модель прокси-моделью
    if adapter_type == "proxy":
        # Получаем конфигурацию модели
        from backend.config.model_config import AVAILABLE_MODELS
        model_config = {}
        
        # Ищем конфигурацию модели в доступных моделях
        for provider, models in AVAILABLE_MODELS.items():
            if model_id in models:
                model_config = models[model_id]
                break
        
        # Получаем базовый URL из конфигурации
        base_url = model_config.get("base_url", "https://api.sree.shop/v1")
        
        # Создаем адаптер для прокси
        return ProxyOpenAIAdapter(model_id=model_id, base_url=base_url)
    elif adapter_type == "openai":
        return OpenAIAdapter(**kwargs)
    elif adapter_type == "anthropic":
        from backend.core.ml_analysis.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(**kwargs)
    elif adapter_type == "huggingface" or adapter_type == "local":
        from backend.core.ml_analysis.model_adapter import HuggingFaceAdapter
        return HuggingFaceAdapter(**kwargs)
    elif adapter_type == "mock":
        return MockAdapter(**kwargs)
    elif adapter_type == "gradio":
        from backend.core.ml_analysis.gradio_adapter import GradioAdapter
        return GradioAdapter(**kwargs)
    else:
        print(f"Неподдерживаемый тип модели: {adapter_type}")
        return MockAdapter(**kwargs)

def create_model(model_id: str) -> BaseModelAdapter:
    """
    Создание модели по идентификатору.
    
    Args:
        model_id: Идентификатор модели
        
    Returns:
        Адаптер для модели
    """
    try:
        # Получаем конфигурацию модели
        model_config = get_model_config(model_id)
        
        # Если модель не найдена, возвращаем мок-адаптер
        if not model_config:
            print(f"Конфигурация модели не найдена для {model_id}, используется мок-адаптер")
            return MockAdapter(model_id=f"mock-{model_id}")
        
        # Проверяем тип модели
        model_type = model_config.get("type", "")
        
        # Если это прокси-модель OpenAI
        if model_id == "gpt-4o-test":
            base_url = model_config.get("base_url", "https://api.sree.shop/v1")
            print(f"Создание прокси-адаптера для {model_id} с использованием модели gpt-4o")
            return ProxyOpenAIAdapter(model_id="gpt-4o", base_url=base_url)
        
        # Для других типов моделей
        return create_adapter(model_type, model_id=model_id, **model_config)
        
    except ImportError as e:
        print(f"Ошибка импорта модуля для модели {model_id}: {str(e)}")
        return MockAdapter(model_id=f"mock-{model_id}")
    except Exception as e:
        print(f"Ошибка создания модели {model_id}: {str(e)}")
        return MockAdapter(model_id=f"mock-{model_id}")