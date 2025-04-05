from typing import Optional, Dict, Any, List
from openai import OpenAI
from backend.config.env import get_env_variable, get_api_key  # Добавляем импорт get_api_key

class ProxyOpenAIAdapter:
    """Адаптер для работы с OpenAI-совместимыми API через прокси."""
    
    def __init__(self, model_id: str = "deepseek-v3", **kwargs):
        """Инициализация адаптера с поддержкой DeepSeek и других моделей через прокси.
        
        Args:
            model_id (str): Идентификатор модели.
            **kwargs: Дополнительные параметры.
        """
        self.model_name = model_id
    
        # Получаем конфигурацию модели
        from backend.config.model_config import get_model_config
        self.model_config = get_model_config(model_id) or {}
        
        # Получаем API ключ сначала из PROXY_API_KEY, затем из API_KEY
        self.api_key = get_env_variable("PROXY_API_KEY", "")
        if not self.api_key:
            self.api_key = get_env_variable("API_KEY", "")
        
        # Проверяем, что API ключ не пустой
        if not self.api_key:
            print("ПРЕДУПРЕЖДЕНИЕ: API ключ для прокси не установлен. Проверьте переменные PROXY_API_KEY или API_KEY в .env файле.")
        
        # Применяем префикс к ключу, если он указан в конфигурации
        key_prefix = self.model_config.get("key_prefix", "")
        if key_prefix and not self.api_key.startswith(key_prefix):
            self.api_key = f"{key_prefix}{self.api_key}"
        
        # Получаем base_url из конфигурации модели или из kwargs
        self.base_url = kwargs.get("base_url", self.model_config.get("base_url", "https://openrouter.ai/api/v1"))
        
        # Получаем дополнительные заголовки из конфигурации
        self.headers = self.model_config.get("headers", {
            "HTTP-Referer": "https://code-review-bot.example.com",
            "X-Title": "Code Review Bot"
        })
        
        # Настройка альтернативных прокси-серверов
        self.alternative_proxies = self._setup_alternative_proxies()
        
        # Создаем клиента с базовым URL и заголовками
        self.client = OpenAI(
            api_key=self.api_key, 
            base_url=self.base_url,
            default_headers=self.headers
        )
        
        print(f"Инициализирован ProxyOpenAIAdapter с моделью: {self.model_name}")
        print(f"API ключ установлен: {'Да' if self.api_key else 'Нет'}")
        print(f"Base URL: {self.base_url}")
        print(f"Дополнительные заголовки: {self.headers}")
        
        # Проверяем доступность сервера
        self._check_connectivity()
    
    def _setup_alternative_proxies(self) -> List[Dict[str, Any]]:
        """Настройка альтернативных прокси-серверов."""
        proxies = [
            {
                "url": "https://openrouter.ai/api/v1",
                "key_prefix": "sk-or-",  # OpenRouter требует префикс sk-or-
                "headers": {
                    "HTTP-Referer": "https://code-review-bot.example.com",
                    "X-Title": "Code Review Bot"
                },
                "model_mapping": {
                    "deepseek-v3": "deepseek/deepseek-v3-base:free",
                    "gpt-4o-proxy": "openai/gpt-4o",
                    "gpt-4o": "openai/gpt-4o"
                }
            },
            {
                "url": "https://api.deepinfra.com/v1/openai",
                "key_prefix": "",  # DeepInfra не требует специального префикса
                "model_mapping": {
                    "deepseek-v3": "deepseek-ai/deepseek-v3-base",
                    "gpt-4o-proxy": "meta-llama/llama-3-70b-instruct",
                    "gpt-4o": "meta-llama/llama-3-70b-instruct"
                }
            }
        ]
        
        print(f"Настроено {len(proxies)} альтернативных прокси-серверов")
        return proxies
        
    def _check_connectivity(self):
        """Проверка доступности API сервера."""
        try:
            # Простой запрос для проверки соединения
            self.client.models.list()
            print("Соединение с API сервером установлено успешно")
        except Exception as e:
            print(f"Предупреждение: не удалось установить соединение с основным API: {str(e)}")
            print("Запросы будут перенаправлены на альтернативные серверы при необходимости")
    
    def analyze(self, prompt, **kwargs):
        """
        Анализ с использованием модели через прокси.
        
        Args:
            prompt: Запрос для анализа.
            **kwargs: Дополнительные параметры.
            
        Returns:
            Результат анализа.
        """
        # Получаем параметры из kwargs или используем значения по умолчанию
        max_tokens = kwargs.get("max_tokens", 2000)
        model_temperature = kwargs.get("temperature", 0.3)
        model_top_p = kwargs.get("top_p", 0.3)
        model_frequency_penalty = kwargs.get("frequency_penalty", 0.3)
        
        # Используем self.api_key вместо получения ключа из переменных окружения
        api_key = self.api_key
        if not api_key:
            # Пробуем получить ключ из переменных окружения как запасной вариант
            api_key = get_env_variable("API_KEY", "")
            if not api_key:
                raise ValueError("API ключ не найден. Установите переменную окружения API_KEY или PROXY_API_KEY.")
        
        # Получаем актуальную модель
        actual_model = self.model_name
        
        # Настраиваем серверы для запросов
        servers_to_try = []
        
        # Добавляем основной сервер OpenAI, если модель не deepseek-v3
        if self.model_name != "deepseek-v3":
            servers_to_try.append({
                "url": "https://api.openai.com/v1",
                "key": api_key,
                "headers": {},
                "model": actual_model
            })
        
        # Добавляем альтернативные прокси-серверы
        proxies = self._setup_alternative_proxies()
        for proxy in proxies:
            # Формируем ключ с префиксом, если он указан
            key = api_key
            if "key_prefix" in proxy and proxy["key_prefix"]:
                if not key.startswith(proxy["key_prefix"]):
                    key = f"{proxy['key_prefix']}{key}"
            
            # Определяем модель для прокси
            proxy_model = actual_model
            if "model_mapping" in proxy and self.model_name in proxy["model_mapping"]:
                proxy_model = proxy["model_mapping"][self.model_name]
                print(f"Используем модель {proxy_model} вместо {actual_model} для {proxy['url']}")
            
            servers_to_try.append({
                "url": proxy["url"],
                "key": key,
                "headers": proxy.get("headers", {}),
                "model": proxy_model
            })
        
        # Перебираем серверы, пока не получим успешный ответ
        last_error = None
        for server in servers_to_try:
            try:
                print(f"Отправка запроса к API с моделью: {server['model']} через {server['url']}")
                print(f"Параметры: temperature={model_temperature}, top_p={model_top_p}, frequency_penalty={model_frequency_penalty}")
                
                # Создаем клиента для текущего сервера
                client = OpenAI(
                    api_key=server["key"],
                    base_url=server["url"],
                    default_headers=server["headers"]
                )
                
                # Отправляем запрос
                response = client.chat.completions.create(
                    model=server["model"],
                    messages=[
                        {"role": "system", "content": "You are a code review assistant that helps identify issues and suggest improvements."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=model_temperature,
                    top_p=model_top_p,
                    frequency_penalty=model_frequency_penalty
                )
                
                # Проверяем ответ
                if response and hasattr(response, 'choices') and response.choices:
                    response_content = response.choices[0].message.content
                    if response_content and response_content.strip():
                        print(f"Получен ответ от API: {response_content[:100]}...")
                        return response_content
                    else:
                        print(f"Получен пустой ответ от сервера {server['url']}. Полный ответ: {response}")
                        continue  # Пробуем следующий сервер
                else:
                    print(f"Получен некорректный ответ от сервера {server['url']}. Ответ: {response}")
            
            except Exception as e:
                error_message = f"Ошибка при использовании сервера {server['url']}: {str(e)}"
                print(error_message)
                last_error = e
                continue  # Пробуем следующий сервер
        
        # Если все серверы не сработали, генерируем соответствующее исключение
        if last_error:
            error_str = str(last_error).lower()
            if "api_key" in error_str or "apikey" in error_str:
                raise ValueError("Неверный или отсутствующий API ключ")
            elif "rate" in error_str and "limit" in error_str:
                raise ValueError("Превышен лимит запросов к API")
            elif "quota" in error_str or "insufficient_quota" in error_str:
                raise ValueError("Превышена квота API")
            elif "model" in error_str and ("access" in error_str or "available" in error_str or "404" in error_str or "not found" in error_str):
                raise ValueError(f"Модель {self.model_name} недоступна или не существует")
            elif "connect" in error_str or "connection" in error_str:
                raise ConnectionError("Проблема с подключением к серверу API")
            elif "timeout" in error_str:
                raise TimeoutError("Превышено время ожидания ответа от сервера")
            else:
                raise Exception(f"Неожиданная ошибка: {str(last_error)}")
        else:
            raise ConnectionError("Не удалось получить ответ от всех доступных серверов")

    def analyze_code(self, code: str, language: str, **kwargs) -> str:
        """
        Анализ кода с использованием DeepSeek или другой модели через прокси.
        
        Args:
            code (str): Код для анализа.
            language (str): Язык программирования.
            **kwargs: Дополнительные параметры.
            
        Returns:
            str: Результат анализа кода.
        """
        try:
            # Получаем язык ответа из параметров
            response_language = kwargs.get('response_language', 'russian')
            
            # Базовая часть промпта одинакова для всех языков - анализ кода
            base_prompt = (
                f"Analyze the following {language} code and suggest improvements:\n\n"
                f"```{language}\n"
                f"{code}\n"
                "```\n\n"
            )
            
            # Формируем запрос в зависимости от выбранного языка ответа
            if response_language == 'bilingual':
                prompt = base_prompt + (
                    "Please provide your response in TWO languages - first in Russian, then in English, separated by a clear divider.\n"
                    "Cover: code quality, potential bugs, performance, security, and best practices.\n\n"
                    "Format your response as follows:\n"
                    "## РУССКИЙ ОТВЕТ\n"
                    "[Полный ответ на русском языке]\n\n"
                    "---\n\n"
                    "## ENGLISH RESPONSE\n"
                    "[Complete response in English]"
                )
            elif response_language == 'english':
                prompt = base_prompt + (
                    "Please provide your response in English only.\n"
                    "Cover: code quality, potential bugs, performance, security, best practices, readability, and any other relevant observations."
                )
            else:  # russian по умолчанию
                prompt = base_prompt + (
                    "Please provide your response in Russian only.\n"
                    "Cover: code quality, potential bugs, performance, security, best practices, readability, and any other relevant observations."
                )
            
            # Получаем параметры из kwargs или используем значения по умолчанию
            max_tokens = kwargs.get("max_tokens", 2000)
            temperature = kwargs.get("temperature", 0.3)
            top_p = kwargs.get("top_p", 0.3)
            frequency_penalty = kwargs.get("frequency_penalty", 0.3)
            
            # Используем self.analyze
            result = self.analyze(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty
            )
            return result
        except Exception as e:
            # Добавляем обработку исключений для отладки
            print(f"Ошибка в методе analyze_code: {str(e)}")
            raise  # Повторно вызываем исключение после логирования