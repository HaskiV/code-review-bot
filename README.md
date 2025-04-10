# Code Review Bot

Автоматический анализ и ревью кода с использованием нейронных сетей. Идеальное решение для небольших команд и стартапов, которые хотят улучшить качество своего кода без использования дорогих корпоративных решений.

## Возможности

- Анализ кода с использованием различных моделей ИИ (OpenAI, Anthropic, HuggingFace и др.)
- Предложения по улучшению кода и выявление потенциальных проблем
- Поддержка нескольких языков программирования (Python, JavaScript, Java, C++, C#, PHP, Ruby)
- Возможность получения результатов анализа на русском, английском или обоих языках
- Простой и удобный веб-интерфейс с подсветкой синтаксиса
- Кэширование результатов для экономии ресурсов и ускорения работы
- Возможность использования локальных моделей для анализа без доступа к интернету

## Архитектура

Проект состоит из двух основных компонентов:

1. **Backend** - Flask-приложение, обрабатывающее запросы и взаимодействующее с моделями ИИ
2. **Frontend** - Веб-интерфейс с использованием CodeMirror для удобного ввода и отображения кода

### Адаптеры моделей

Система использует различные адаптеры для работы с разными моделями:

- `OpenAIAdapter` - для работы с моделями OpenAI (GPT-4, GPT-3.5)
- `AnthropicAdapter` - для работы с моделями Claude
- `HuggingFaceAdapter` - для работы с моделями HuggingFace
- `ProxyAdapter` - для работы через прокси-сервер
- `MockAdapter` - для тестирования без использования реальных моделей
- `GradioAdapter` - для работы с моделями через Gradio API

## Требования

- Python 3.8+
- Docker и Docker Compose (опционально)
- API ключи для используемых сервисов:
  - OpenAI API Key
  - Anthropic API Key
  - HuggingFace API Key
  - Proxy API Key (если используется)

## Установка и запуск

### С использованием Docker

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/code-review-bot.git
   cd code-review-bot
   ```
   
2. Настройте переменные окружения:
   - Скопируйте файл `.env.example` в `.env`
   - Заполните необходимые API ключи и настройки
   
3. Запустите с помощью Docker Compose:
   ```bash
   docker-compose up --build
   ```
   
4. Откройте веб-браузер и перейдите по адресу http://localhost:5000

### Локальная установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/code-review-bot.git
   cd code-review-bot
   ```
   
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
   
3. Настройте переменные окружения:
   - Скопируйте файл `.env.example` в `.env`
   - Заполните необходимые API ключи и настройки
   
4. Запустите приложение:
   ```bash
   cd backend
   python app.py
   ```
   
5. Откройте веб-браузер и перейдите по адресу http://localhost:5000

## Конфигурация

Основные настройки приложения хранятся в файле `.env`:

```plaintext
ENVIRONMENT=development
DEBUG_MODE=False
PORT=5000
HOST=0.0.0.0
LOG_LEVEL=INFO
MAX_CODE_LENGTH=10000
REQUEST_TIMEOUT=60
CACHE_EXPIRY=3600
PROXY_API_KEY=YOUR_PROXY_API_KEY
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY
HUGGINGFACE_API_KEY=YOUR_HUGGINGFACE_API_KEY
```

## Использование

1. Выберите язык программирования из выпадающего списка
2. Вставьте ваш код в текстовое поле
3. Выберите модель для анализа
4. Выберите язык ответа (русский, английский или двуязычный)
5. Нажмите кнопку "Анализировать код"
6. Получите результаты анализа и предложения по улучшению

## Поддерживаемые языки программирования

- Python
- JavaScript
- Java
- C++
- C#
- PHP
- Ruby

## API

### Анализ кода

```plaintext
POST /api/review
```

Параметры запроса:

- `code` (string): Код для анализа
- `language` (string): Язык программирования
- `model` (string, optional): Идентификатор модели для анализа
- `response_language` (string, optional): Язык ответа (russian, english, bilingual)

Пример ответа:

```json
{
  "success": true,
  "result": "# Анализ кода\n\n## Качество кода\n...",
  "model": "gpt-4o"
}
```

## Расширение функциональности

### Добавление новой модели

1. Создайте новый адаптер в директории `backend/core/ml_analysis/`
2. Реализуйте метод `analyze_code()`
3. Зарегистрируйте модель в сервисе `ModelService`

### Добавление поддержки нового языка программирования

1. Добавьте язык в выпадающий список в `frontend/index.html`
2. При необходимости добавьте специфичные для языка промпты в адаптеры моделей

## Устранение неполадок

### Ошибка подключения к API

Убедитесь, что:

- API ключи правильно указаны в файле `.env`
- У вас есть доступ к интернету
- Сервисы API доступны и работают

### Ошибка "Model not available"

Убедитесь, что выбранная модель зарегистрирована в системе и доступна для использования.

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для вашей функциональности (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add some amazing feature'`)
4. Отправьте изменения в ваш форк (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## Лицензия

MIT License
