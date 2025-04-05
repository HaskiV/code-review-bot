from abc import ABC, abstractmethod
import sys
import os
import json
import logging
import hashlib
import torch
from pathlib import Path
from typing import Dict, Any, Optional, Union
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel, T5ForConditionalGeneration

# Импортируем улучшенные модули конфигурации
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from backend.config.env import get_api_key, get_request_timeout, is_debug_mode
from backend.config.model_config import (
    get_model_parameters, 
    get_prompt_template, 
    get_response_parsing_config,
    get_local_model_config,
    is_caching_enabled,
    get_cache_settings
)

# Настройка логирования
logger = logging.getLogger(__name__)

# Определение типа модели
ModelType = Union[AutoModelForCausalLM, AutoModel]

class ModelAdapter(ABC):
    """Базовый адаптер для работы с моделями."""
    
    def __init__(self):
        """Инициализация базового адаптера."""
        self.cache_dir = Path(get_cache_settings().get("cache_dir", "cache"))
        self.cache_enabled = is_caching_enabled()
        
        # Создаем директорию для кэша, если она не существует
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    @abstractmethod
    def analyze_code(self, code: str, language: str) -> str:
        """
        Абстрактный метод для анализа кода.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        pass
    
    def _create_prompt(self, code: str, language: str) -> str:
        """
        Создание промпта для модели на основе кода и языка.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Промпт для модели
        """
        # Базовый промпт по умолчанию
        return f"""Проанализируйте следующий код на языке {language} и предложите улучшения:

```{language}
{code}
```"""

    def _parse_response(self, response: str) -> str:
        """
        Разбор ответа модели в структурированный формат.
        
        Args:
            response: Ответ модели
            
        Returns:
            Структурированный ответ
        """
        return response
    
    def _get_cache_key(self, code: str, language: str) -> str:
        """
        Создание ключа кэша на основе кода и языка.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Ключ кэша
        """
        # Создаем хэш на основе кода, языка и имени класса
        content = f"{self.__class__.__name__}:{language}:{code}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, code: str, language: str) -> Optional[str]:
        """
        Получение результата из кэша.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Кэшированный результат или None, если кэш не найден
        """
        if not self.cache_enabled:
            return None
            
        cache_key = self._get_cache_key(code, language)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Проверяем срок действия кэша
                import time
                current_time = time.time()
                cache_time = cache_data.get("timestamp", 0)
                cache_expiry = get_cache_settings().get("expiry_time", 3600)
                
                if current_time - cache_time <= cache_expiry:
                    logger.debug(f"Используется кэшированный результат для {language}")
                    return cache_data.get("result")
            except Exception as e:
                logger.warning(f"Ошибка при чтении кэша: {str(e)}")
                
        return None
    
    def _save_to_cache(self, code: str, language: str, result: str) -> None:
        """
        Сохранение результата в кэш.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            result: Результат анализа
        """
        if not self.cache_enabled:
            return
            
        cache_key = self._get_cache_key(code, language)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            import time
            cache_data = {
                "result": result,
                "timestamp": time.time(),
                "language": language
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"Результат сохранен в кэш для {language}")
        except Exception as e:
            logger.warning(f"Ошибка при сохранении в кэш: {str(e)}")


class OpenAIAdapter(ModelAdapter):
    """Адаптер для работы с API OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Инициализация адаптера OpenAI.
        
        Args:
            api_key: API ключ OpenAI (если None, будет получен из конфигурации)
            model: Имя модели OpenAI
        """
        super().__init__()
        try:
            from openai import OpenAI
            
            # Получаем API ключ из конфигурации, если не передан
            self.api_key = api_key or get_api_key("openai")
            if not self.api_key:
                raise ValueError("API ключ OpenAI не найден. Укажите его в .env или secrets.json")
                
            self.model = model
            self.client = OpenAI(api_key=self.api_key)
            
            # Получаем параметры модели из конфигурации
            self.model_params = get_model_parameters("openai", model) or {}
            
            logger.info(f"Адаптер OpenAI инициализирован с моделью {model}")
        except ImportError:
            raise ImportError("Пакет OpenAI не установлен. Установите его с помощью 'pip install openai'")

    def _create_prompt(self, code: str, language: str) -> Dict[str, Any]:
        """
        Создание промпта для OpenAI на основе шаблона из конфигурации.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Словарь с сообщениями для API OpenAI
        """
        # Получаем шаблон промпта из конфигурации
        template = get_prompt_template("openai") or {}
        
        system_message = template.get("system_message", 
            "You are a code review assistant specialized in identifying bugs, suggesting improvements, and ensuring code quality.")
            
        user_template = template.get("user_message", super()._create_prompt(code, language))
        user_message = user_template.format(language=language, code=code)
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

    def analyze_code(self, code: str, language: str) -> str:
        """
        Анализ кода с использованием API OpenAI.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        # Проверяем кэш
        cached_result = self._get_from_cache(code, language)
        if cached_result:
            return cached_result
            
        # Создаем промпт
        messages = self._create_prompt(code, language)
        
        try:
            # Получаем параметры из конфигурации или используем значения по умолчанию
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.model_params.get("temperature", 0.3),
                "max_tokens": self.model_params.get("max_tokens", 2048),
                "top_p": self.model_params.get("top_p", 1.0),
                "frequency_penalty": self.model_params.get("frequency_penalty", 0.0),
                "presence_penalty": self.model_params.get("presence_penalty", 0.0)
            }
            
            # Устанавливаем таймаут из конфигурации
            timeout = get_request_timeout()
            
            # Выполняем запрос к API
            response = self.client.chat.completions.create(**params, timeout=timeout)
            result = self._parse_response(response.choices[0].message.content)
            
            # Сохраняем результат в кэш
            self._save_to_cache(code, language, result)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка при анализе кода с OpenAI: {str(e)}")
            return f"Ошибка при анализе кода с OpenAI: {str(e)}"


class AnthropicAdapter(ModelAdapter):
    """Адаптер для работы с API Anthropic."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """
        Инициализация адаптера Anthropic.
        
        Args:
            api_key: API ключ Anthropic (если None, будет получен из конфигурации)
            model: Имя модели Anthropic
        """
        super().__init__()
        try:
            from anthropic import Anthropic
            
            # Получаем API ключ из конфигурации, если не передан
            self.api_key = api_key or get_api_key("anthropic")
            if not self.api_key:
                raise ValueError("API ключ Anthropic не найден. Укажите его в .env или secrets.json")
                
            self.model = model
            self.client = Anthropic(api_key=self.api_key)
            
            # Получаем параметры модели из конфигурации
            self.model_params = get_model_parameters("anthropic", model) or {}
            
            logger.info(f"Адаптер Anthropic инициализирован с моделью {model}")
        except ImportError:
            raise ImportError("Пакет Anthropic не установлен. Установите его с помощью 'pip install anthropic'")
    
    def _create_prompt(self, code: str, language: str) -> str:
        """
        Создание промпта для Anthropic на основе шаблона из конфигурации.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Промпт для API Anthropic
        """
        # Получаем шаблон промпта из конфигурации
        template = get_prompt_template("anthropic") or {}
        
        user_template = template.get("user_message", super()._create_prompt(code, language))
        return user_template.format(language=language, code=code)
    
    def analyze_code(self, code: str, language: str) -> str:
        """
        Анализ кода с использованием API Anthropic.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        # Проверяем кэш
        cached_result = self._get_from_cache(code, language)
        if cached_result:
            return cached_result
            
        # Создаем промпт
        prompt = self._create_prompt(code, language)
        
        try:
            # Получаем параметры из конфигурации или используем значения по умолчанию
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.model_params.get("temperature", 0.3),
                "max_tokens": self.model_params.get("max_tokens", 4000),
                "top_p": self.model_params.get("top_p", 0.95)
            }
            
            # Добавляем top_k, если он есть в параметрах
            if "top_k" in self.model_params:
                params["top_k"] = self.model_params["top_k"]
            
            # Устанавливаем таймаут из конфигурации
            timeout = get_request_timeout()
            
            # Выполняем запрос к API
            response = self.client.messages.create(**params)
            result = self._parse_response(response.content[0].text)
            
            # Сохраняем результат в кэш
            self._save_to_cache(code, language, result)
            
            return result
        except Exception as e:
            logger.error(f"Ошибка при анализе кода с Anthropic: {str(e)}")
            return f"Ошибка при анализе кода с Anthropic: {str(e)}"


class HuggingFaceAdapter(ModelAdapter):
    """Адаптер для работы с моделями Hugging Face."""
    
    def __init__(self, model_name: str, device: str = "cpu", quantization: Optional[str] = None):
        """
        Инициализация адаптера Hugging Face.
        
        Args:
            model_name: Имя модели или путь к локальной модели
            device: Устройство для запуска модели (cpu или cuda)
            quantization: Тип квантизации (4bit, 8bit или None)
        """
        super().__init__()
        
        # Проверяем, что параметры корректны
        print(f"Инициализация HuggingFaceAdapter с model_name={model_name}, device={device}, quantization={quantization}")
        
        # Загружаем модель и токенизатор
        self.model_name = model_name
        self.device = device
        self.quantization = quantization
        
        # Загружаем параметры модели
        self.model_params = get_model_parameters("huggingface")
        
        # Инициализируем токенизатор и модель
        self.tokenizer = None
        self.model = None
        
        # Загружаем токенизатор и модель
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели и токенизатора."""
        try:
            print(f"Загрузка токенизатора из {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            print(f"Загрузка модели из {self.model_name} с device={self.device}, quantization={self.quantization}")
            
            # Настройка параметров загрузки модели
            model_kwargs = {}
            
            # Для CPU используем специальные оптимизации без device_map
            if self.device == "cpu":
                print("Используется CPU, загрузка модели с базовыми настройками CPU")
                model_kwargs.update({
                    "low_cpu_mem_usage": True,
                    "torch_dtype": torch.float32,  # Используем float32 для CPU
                    # Не используем device_map или offload для CPU
                })
            else:
                # Для CUDA используем квантизацию и float16
                model_kwargs.update({
                    "device_map": self.device,
                    "torch_dtype": torch.float16
                })
                if self.quantization:
                    from transformers import BitsAndBytesConfig
                    if self.quantization == "4bit":
                        model_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16
                        )
                    elif self.quantization == "8bit":
                        model_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_8bit=True
                        )
            
            # Пробуем загрузить модель как AutoModelForCausalLM
            try:
                print("Попытка загрузки как AutoModelForCausalLM")
                from transformers import AutoModelForCausalLM
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    **model_kwargs
                )
                print("Модель успешно загружена как AutoModelForCausalLM")
            except Exception as e:
                print(f"Ошибка загрузки как AutoModelForCausalLM: {str(e)}")
                
                # Если не удалось, пробуем загрузить как обычную модель
                print("Попытка загрузки как AutoModel")
                from transformers import AutoModel
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    **model_kwargs
                )
                print("Модель успешно загружена как AutoModel")
            
            print(f"Модель и токенизатор успешно загружены")
        except Exception as e:
            print(f"Ошибка загрузки модели и токенизатора: {str(e)}")
            raise
    
    def analyze_code(self, code: str, language: str) -> str:
        """
        Анализ кода с использованием модели Hugging Face.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        # Проверяем кэш
        cached_result = self._get_from_cache(code, language)
        if cached_result:
            return cached_result
            
        # Создаем промпт
        prompt = self._create_prompt(code, language)
        
        try:
            # Токенизируем промпт
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Генерируем ответ
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=self.model_params.get("max_length", 2048),
                    temperature=self.model_params.get("temperature", 0.7),
                    top_p=self.model_params.get("top_p", 0.95),
                    top_k=self.model_params.get("top_k", 50),
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Декодируем ответ
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Удаляем промпт из ответа
            result = result.replace(prompt, "").strip()
            
            # Разбираем ответ в структурированный формат
            parsed_result = self._parse_response(result)
            
            # Сохраняем результат в кэш
            self._save_to_cache(code, language, parsed_result)
            
            return parsed_result
        except Exception as e:
            logger.error(f"Ошибка при анализе кода с {self.model_name}: {str(e)}")
            return f"Ошибка при анализе кода с {self.model_name}: {str(e)}"


class MockAdapter(ModelAdapter):
    """Мок-адаптер для тестирования без реальных моделей."""
    
    def __init__(self, language_specific_responses: Optional[Dict[str, str]] = None):
        """
        Инициализация мок-адаптера.
        
        Args:
            language_specific_responses: Словарь с ответами для конкретных языков
        """
        super().__init__()
        self.language_specific_responses = language_specific_responses or {}
        logger.info("Мок-адаптер инициализирован")
    
    def analyze_code(self, code: str, language: str) -> str:
        """
        Анализ кода с использованием мок-ответов.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        # Проверяем кэш
        cached_result = self._get_from_cache(code, language)
        if cached_result:
            return cached_result
            
        # Используем специфичный для языка ответ, если он есть
        if language in self.language_specific_responses:
            result = self.language_specific_responses[language]
        else:
            # Генерируем базовый ответ
            lines = code.split('\n')
            result = f"""
            Тестовый режим анализа кода на языке {language}.
            
            Рекомендации по улучшению:
            1. Добавьте больше комментариев для улучшения читаемости
            2. Следуйте стандартам форматирования {language}
            3. Рассмотрите возможность разделения длинных функций на более мелкие
            4. Используйте более описательные имена переменных
            
            Метрики кода:
            - Строк кода: {len(lines)}
            - Средняя длина строки: {sum(len(line) for line in lines) / max(len(lines), 1):.1f} символов
            
            Это тестовый вывод для проверки функциональности интерфейса.
            """
        
        # Сохраняем результат в кэш
        self._save_to_cache(code, language, result)
        
        return result


def create_adapter(provider: str, **kwargs) -> ModelAdapter:
    """
    Фабричный метод для создания адаптера модели.
    
    Args:
        provider: Провайдер модели ("openai", "anthropic", "huggingface", "mock")
        **kwargs: Дополнительные параметры для адаптера
        
    Returns:
        Экземпляр адаптера модели
    """
    if provider == "openai":
        return OpenAIAdapter(**kwargs)
    elif provider == "anthropic":
        return AnthropicAdapter(**kwargs)
    elif provider == "huggingface":
        return HuggingFaceAdapter(**kwargs)
    elif provider == "mock":
        return MockAdapter(**kwargs)
    else:
        raise ValueError(f"Неизвестный провайдер модели: {provider}")