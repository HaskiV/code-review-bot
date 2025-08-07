from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
# Исправляем импорты, убирая относительные пути
from backend.core.ml_analysis.model_adapter import create_adapter
from backend.config.env import get_api_key, get_env_variable
from backend.celery_app import celery

@celery.task
def load_model_task(model_id, model_config):
    """Celery task to load a model adapter."""
    try:
        create_adapter(model_config['type'], model_id=model_id, model_config=model_config)
        print(f"Successfully preloaded model: {model_id}")
    except Exception as e:
        print(f"Error preloading model {model_id}: {e}")

class ModelService:
    """Сервис для работы с моделями анализа кода."""
    
    def __init__(self, models_file=None):
        """
        Инициализация сервиса моделей.
        
        Args:
            models_file: Путь к файлу с конфигурацией моделей
        """
        self.models_file = models_file or Path(__file__).parent.parent / "data" / "models.json"
        self.models = {}
        self.default_model = None
        self.adapters = {}
        self.load_model_configs()

    def preload_models_in_background(self):
        """Dispatches Celery tasks to preload all models."""
        for model_id, model_config in self.models.items():
            if model_config.get('type') != 'mock': # Don't preload mock models
                load_model_task.delay(model_id, model_config)

    def get_adapter(self, model_id=None):
        """
        Получение адаптера для модели.
        
        Args:
            model_id: Идентификатор модели
            
        Returns:
            Адаптер для модели
        """
        model_id = model_id or self.default_model
        
        if model_id not in self.models:
            model_id = self.default_model
        
        if model_id not in self.adapters:
            model_data = self.models[model_id]
            # Создаем адаптер для других типов моделей
            from backend.core.ml_analysis.adapter_factory import create_adapter
            self.adapters[model_id] = create_adapter(model_data['type'], model_id=model_id, model_config=model_data)
        
        return self.adapters[model_id]
    
    def analyze_code(self, code: str, language: str, model_id: str = None, **kwargs) -> str:
        """
        Анализирует код с использованием выбранной модели.
        
        Args:
            code (str): Код для анализа
            language (str): Язык программирования
            model_id (str, optional): Идентификатор модели
            **kwargs: Дополнительные параметры
            
        Returns:
            str: Результат анализа
        """
        if not model_id:
            model_id = self.default_model
        
        print(f"Analyzing code with model: {model_id}")
        
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not available. Available models: {list(self.models.keys())}")
            
            # Получаем адаптер для модели
            adapter = self.get_adapter(model_id)
            
            # Не нужно извлекать response_language отдельно, так как он уже есть в kwargs
            result = adapter.analyze_code(
                code, 
                language, 
                **kwargs  # Передаем все kwargs напрямую, включая response_language
            )
            
            return result
        except Exception as e:
            print(f"Error analyzing code with {model_id}: {str(e)}")
            print("Falling back to mock model")
            
            # Если произошла ошибка, используем mock-модель
            return self._get_mock_analysis(code, language)
        
    def _get_mock_analysis(self, code, language):
        """
        Получение заглушки для анализа кода (для тестирования).
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Заглушка для анализа кода
        """
        return f"""# Анализ кода (Mock)
    
    ## Качество кода
    - Код написан в хорошем стиле
    - Следует стандартам форматирования
    
    ## Потенциальные ошибки
    - Не обнаружено явных ошибок
    
    ## Производительность
    - Код выглядит оптимизированным
    
    ## Безопасность
    - Не обнаружено проблем безопасности
    
    ## Рекомендации
    - Добавьте больше комментариев для улучшения читаемости
    - Рассмотрите возможность добавления тестов
    
    *Это заглушка для анализа кода. Используйте другую модель для реального анализа.*
    """
    
    def list_models(self):
        """
        Получение списка всех доступных моделей.
        
        Returns:
            Список моделей
        """
        models_list = []
        for model_id, model_data in self.models.items():
            # Не включаем конфиденциальную информацию (API ключи)
            model_info = {
                "id": model_id,
                "name": model_data["name"],
                "type": model_data["type"],
                "is_default": model_data.get("is_default", False)
            }
            models_list.append(model_info)
        
        return models_list
    
    def add_model(self, model_id, name, model_type, config=None, is_default=False):
        """
        Добавление новой модели.
        
        Args:
            model_id: Идентификатор модели
            name: Название модели
            model_type: Тип модели
            config: Конфигурация модели
            is_default: Является ли модель моделью по умолчанию
            
        Returns:
            Кортеж (успех, сообщение)
        """
        if model_id in self.models:
            return False, f"Модель с идентификатором '{model_id}' уже существует"
        
        self.models[model_id] = {
            "id": model_id,
            "name": name,
            "type": model_type,
            "config": config or {},
            "is_default": is_default
        }
        
        if is_default:
            # Сбрасываем флаг is_default для других моделей
            for other_id in self.models:
                if other_id != model_id:
                    self.models[other_id]["is_default"] = False
            
            self.default_model = model_id
        
        self.save_models()
        
        # Удаляем адаптер из кэша, если он существует
        if model_id in self.adapters:
            del self.adapters[model_id]
        
        return True, f"Модель '{name}' успешно добавлена"
    
    def update_model(self, model_id, name=None, model_type=None, config=None, is_default=None):
        """
        Обновление существующей модели.
        
        Args:
            model_id: Идентификатор модели
            name: Новое название модели
            model_type: Новый тип модели
            config: Новая конфигурация модели
            is_default: Новое значение флага is_default
            
        Returns:
            Кортеж (успех, сообщение)
        """
        if model_id not in self.models:
            return False, f"Модель с идентификатором '{model_id}' не найдена"
        
        model_data = self.models[model_id]
        
        if name is not None:
            model_data["name"] = name
        
        if model_type is not None:
            model_data["type"] = model_type
        
        if config is not None:
            model_data["config"] = config
        
        if is_default is not None:
            model_data["is_default"] = is_default
            
            if is_default:
                # Сбрасываем флаг is_default для других моделей
                for other_id in self.models:
                    if other_id != model_id:
                        self.models[other_id]["is_default"] = False
                
                self.default_model = model_id
        
        self.save_models()
        
        # Удаляем адаптер из кэша, если он существует
        if model_id in self.adapters:
            del self.adapters[model_id]
        
        return True, f"Модель '{model_data['name']}' успешно обновлена"
    
    def delete_model(self, model_id):
        """
        Удаление модели.
        
        Args:
            model_id: Идентификатор модели
            
        Returns:
            Кортеж (успех, сообщение)
        """
        if model_id not in self.models:
            return False, f"Модель с идентификатором '{model_id}' не найдена"
        
        model_data = self.models[model_id]
        
        # Проверяем, является ли модель моделью по умолчанию
        if model_data.get("is_default", False):
            return False, "Невозможно удалить модель по умолчанию"
        
        # Удаляем модель
        del self.models[model_id]
        
        # Удаляем адаптер из кэша, если он существует
        if model_id in self.adapters:
            del self.adapters[model_id]
        
        self.save_models()
        
        return True, f"Модель '{model_data['name']}' успешно удалена"
    
    def load_model_configs(self):
        """Загрузка доступных моделей."""
        from backend.config.model_config import LOCAL_MODELS, AVAILABLE_MODELS, get_local_model_path
        
        self.models = {}
        self.default_model = None
        
        # Проверяем наличие локальных моделей
        for model_id, model_config in LOCAL_MODELS.items():
            model_path = get_local_model_path(model_id)
            
            if model_path and Path(model_path).exists():
                self.models[model_id] = {
                    "id": model_id,
                    "name": model_config.get("name", model_id),
                    "type": model_config.get("type", "unknown"),
                    "path": model_path,
                    "description": model_config.get("description", ""),
                    "is_default": model_config.get("is_default", False)
                }
                
                # Устанавливаем модель по умолчанию
                if model_config.get("is_default", False) and not self.default_model:
                    self.default_model = model_id
                
                print(f"Loaded model: {model_id} from {model_path}")
            else:
                print(f"Model {model_id} not found at {model_path}")
        
        # Загружаем модели из AVAILABLE_MODELS
        for provider, provider_models in AVAILABLE_MODELS.items():
            for model_id, model_config in provider_models.items():
                # Пропускаем, если модель уже загружена
                if model_id in self.models:
                    continue
                    
                # Добавляем модель в список
                self.models[model_id] = {
                    "id": model_id,
                    "name": model_config.get("name", model_id),
                    "type": provider if provider != "gradio" else "gradio",
                    "description": model_config.get("description", ""),
                    "is_default": model_config.get("is_default", False),
                    # Добавляем специфичные для Gradio параметры
                    "api_url": model_config.get("api_url") if provider == "gradio" else None
                }
                
                # Устанавливаем модель по умолчанию
                if model_config.get("is_default", False) and not self.default_model:
                    self.default_model = model_id
                    
                print(f"Loaded API model: {model_id} ({provider})")
        
        # Если нет моделей, добавляем заглушку
        if not self.models:
            mock_model_id = "mock-model"
            self.models[mock_model_id] = {
                "id": mock_model_id,
                "name": "Mock Model",
                "type": "mock",
                "description": "Заглушка для тестирования без реальных моделей",
                "is_default": True
            }
            self.default_model = mock_model_id
            print("No models found, using mock model")
        
        print(f"Available models: {list(self.models.keys())}")
        print(f"Default model: {self.default_model}")
    
    def get_models(self):
        """
        Получение списка доступных моделей.
        
        Returns:
            list: Список моделей в формате словарей
        """
        models_list = []
        for model_id, model_data in self.models.items():
            models_list.append({
                "id": model_id,
                "name": model_data.get("name", model_id),
                "description": model_data.get("description", ""),
                "is_default": model_id == self.default_model
            })
        
        print(f"Returning models: {models_list}")
        return models_list
    
    def get_default_model(self):
        """
        Получение идентификатора модели по умолчанию.
        
        Returns:
            str: Идентификатор модели по умолчанию
        """
        return self.default_model


    def _get_mock_analysis(self, code, language):
        """Возвращает заглушку анализа кода для тестирования."""
        return {
            "analysis": [
                {
                    "category": "Code Quality",
                    "issues": [
                        {
                            "title": "Тестовый анализ кода",
                            "description": "Это тестовый анализ, сгенерированный заглушкой.",
                            "severity": "info"
                        }
                    ]
                }
            ],
            "summary": "Это тестовый анализ кода, сгенерированный заглушкой ModelService.",
            "model_info": {
                "name": "Mock Model",
                "type": "mock"
            }
        }
