from typing import Optional
from openai import OpenAI
from backend.config.env import get_api_key, get_env_variable

class OpenAIAdapter:
    """Адаптер для работы с OpenAI API."""
    
    def __init__(self, model_id: str = "gpt-4o mini", **kwargs):
        """Инициализация адаптера OpenAI."""
        self.model_name = model_id
        # Используем get_api_key вместо get_env_variable
        self.api_key = get_api_key("openai")
        if not self.api_key:
            # Для обратной совместимости проверяем старый способ
            self.api_key = get_env_variable("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=self.api_key)
        
    def analyze_code(self, code: str, language: str, **kwargs) -> str:
        """
        Анализ кода с использованием OpenAI API.
        
        Args:
            code (str): Код для анализа
            language (str): Язык программирования
            **kwargs: Дополнительные параметры
            
        Returns:
            str: Результат анализа кода
        """
        # Формируем запрос для анализа кода
        prompt = f"""Analyze the following {language} code and suggest improvements:

```{language}
{code}
```
Please provide:

1. Code quality issues
2. Potential bugs
3. Performance improvements
4. Security concerns
5. Best practices recommendations
   """
   # Получаем максимальное количество токенов из kwargs или используем значение по умолчанию
        max_tokens = kwargs.get('max_tokens', 2000)
        # Получаем уровень сложности из kwargs или используем значение по умолчанию
        temperature = kwargs.get('temperature', 0.3)
        # Получаем уровень сложности из kwargs или используем значение по умолчанию
        top_p = kwargs.get('top_p', 0.3)
        # Получаем уровень сложности из kwargs или используем значение по умолчанию
        frequency_penalty = kwargs.get('frequency_penalty', 0.3)
        # Вызываем метод analyze для выполнения запроса
        return self.analyze(prompt, max_tokens=max_tokens, temperature=temperature)

    def analyze(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        """
        Анализ кода с использованием OpenAI API.

        Args:
            prompt (str): Запрос для анализа
            max_tokens (int, optional): Максимальное количество токенов в ответе
            temperature (float): Уровень творчества модели
        """
        if not self.api_key:
            print("Ошибка: Ключ OpenAI API не установлен")
            raise ValueError("OpenAI API key is not set")
        try:
            print(f"Sending request to OpenAI API with model: {self.model_name}")
            # Main API call logic
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature)
            # Validate response
            if not response or not hasattr(response, 'choices') or not response.choices:
                print("Ошибка: Некорректный ответ от OpenAI API")
                raise ValueError("Invalid response from OpenAI API")
            
            response_content = response.choices[0].message.content
            print(f"Получен ответ от OpenAI API: {response_content[:100]}...")
            # Возвращаем содержимое ответа от API
            return response_content
        except Exception as e:
            print(f"Ошибка в запросе OpenAI API: {str(e)}")
     # Проверяем, связана ли ошибка с API ключом
            if "api_key" in str(e).lower() or "apikey" in str(e).lower():
                print("Ошибка: Неверный или отсутствующий ключ OpenAI API. Пожалуйста, проверьте настройки вашего API ключа.")
     # Проверяем, связана ли ошибка с ограничениями скорости
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                print("Ошибка: Превышен лимит запросов к OpenAI API. Пожалуйста, попробуйте позже.")
     # Проверяем, связана ли ошибка с квотой
            elif "quota" in str(e).lower():
                print("Ошибка: Превышена квота OpenAI API. Пожалуйста, проверьте информацию о вашем биллинге.")
     # Проверяем, связана ли ошибка с доступом к модели
            elif "model" in str(e).lower() and ("access" in str(e).lower() or "available" in str(e).lower()):
                print(f"Ошибка: У вас нет доступа к модели {self.model_name}. Попробуйте использовать другую модель.")
        raise