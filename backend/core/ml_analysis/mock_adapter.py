from typing import Optional

class MockAdapter:
    """Мок-адаптер для тестирования без реальных API-вызовов."""
    
    def __init__(self, model_id: str = "mock-model", **kwargs):
        """Инициализация мок-адаптера."""
        self.model_name = model_id
        print(f"Инициализирован MockAdapter с моделью: {model_id}")
        
    def analyze_code(self, code: str, language: str, **kwargs) -> str:
        """
        Мок-анализ кода.
        
        Args:
            code (str): Код для анализа
            language (str): Язык программирования
            **kwargs: Дополнительные параметры
            
        Returns:
            str: Результат мок-анализа
        """
        print(f"MockAdapter: Анализ {len(code)} символов кода на языке {language}")
        return f"""# Мок-обзор кода на языке {language}

## Качество кода
- Это мок-обзор, сгенерированный MockAdapter
- Реальный анализ не выполнялся

## Потенциальные проблемы
- Это только заглушка для целей тестирования
- Для реального анализа используйте другую модель

## Рекомендации
- Переключитесь на рабочую модель, например 'gpt-4o' или 'claude-3-7'
- Проверьте ваши API-ключи и сетевое подключение
"""
        
    def analyze(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        """
        Мок-анализ с общим запросом.

        Args:
            prompt (str): Запрос для анализа
            max_tokens (int, optional): Максимальное количество токенов в ответе
            temperature (float): Параметр температуры для вариативности ответа
            
        Returns:
            str: Мок-ответ
        """
        print(f"MockAdapter: Обработка запроса длиной {len(prompt)} символов")
        return "Это мок-ответ от MockAdapter. Реальная модель ИИ не использовалась."