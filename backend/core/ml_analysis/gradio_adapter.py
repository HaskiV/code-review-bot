"""
Адаптер для работы с моделями через Gradio API.
"""
from typing import Dict, Any, Optional
import json
from gradio_client import Client

from backend.core.ml_analysis.model_adapter import ModelAdapter

class GradioAdapter(ModelAdapter):
    """Адаптер для работы с моделями через Gradio API."""
    
    def __init__(self, api_url: str, model_id: str = None):
        """
        Инициализация адаптера Gradio.
        
        Args:
            api_url: URL Gradio API
            model_id: Идентификатор модели
        """
        super().__init__()
        self.api_url = api_url
        self.model_id = model_id
        self.client = Client(api_url)
        
    def analyze_code(self, code: str, language: str) -> str:
        """
        Анализ кода с использованием модели через Gradio API.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Результат анализа кода
        """
        # Получаем кэшированный результат, если он есть
        cached_result = self._get_from_cache(code, language)
        if cached_result:
            return cached_result
        
        # Создаем промпт для модели
        prompt = self._create_prompt(code, language)
        
        try:
            # Отправляем запрос к Gradio API
            result = self.client.predict(
                message=prompt,
                param_2=10000,  # Максимальная длина контекста
                param_3=8000,   # Максимальная длина ответа
                api_name="/chat"
            )
            
            # Разбираем ответ в структурированный формат
            parsed_result = self._parse_response(result)
            
            # Сохраняем результат в кэш
            self._save_to_cache(code, language, parsed_result)
            
            return parsed_result
        except Exception as e:
            print(f"Error in Gradio API request: {str(e)}")
            raise
            
    def _create_prompt(self, code: str, language: str) -> str:
        """
        Создание промпта для модели.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования
            
        Returns:
            Промпт для модели
        """
        return f"""Analyze the following {language} code and provide a detailed code review:

```{language}
{code}
```
Пожалуйста, предоставьте ваш анализ в следующем формате:

1. Качество кода - Комментарии по стилю, читаемости и соответствию лучшим практикам
2. Потенциальные ошибки - Выявление любых ошибок или логических проблем
3. Производительность - Предложения по улучшению производительности
4. Безопасность - Выявление уязвимостей безопасности
5. Рекомендации - Предложите конкретные улучшения с примерами кода
   Ваш анализ должен быть тщательным и конкретным для предоставленного кода."""