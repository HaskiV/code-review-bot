import click
from flask.cli import with_appcontext
from pathlib import Path
import torch
import os

@click.command('download-model')
@click.argument('model_id')
@click.option('--token', help='Токен Hugging Face для доступа к закрытым моделям')
@click.option('--revision', default='main', help='Ревизия/ветка модели для загрузки')
@click.option('--force', is_flag=True, help='Принудительная повторная загрузка, даже если модель существует')
@click.option('--cache-dir', help='Пользовательская директория кэша для загруженных моделей')
@with_appcontext
def download_model_command(model_id, token, revision, force, cache_dir):
    """Загрузка локальной модели из Hugging Face."""
    from backend.config.env import BASE_DIR
    from backend.config.model_config import LOCAL_MODELS, get_local_model_path, HUGGINGFACE_TOKEN
    
    if model_id not in LOCAL_MODELS:
        click.echo(f"Ошибка: Модель {model_id} не найдена в конфигурации")
        return
    
    model_config = LOCAL_MODELS[model_id]
    model_path = get_local_model_path(model_id)
    
    if not model_path:
        click.echo(f"Ошибка: Неверный путь к модели для {model_id}")
        return
    
    # Проверка существования модели
    if Path(model_path).exists() and not force:
        click.echo(f"Модель {model_id} уже существует по пути {model_path}")
        click.echo("Используйте --force для повторной загрузки")
        return
    
    # Создание директории для модели
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"Загрузка модели {model_id} в {model_path}...")
    
    # Определение репозитория Hugging Face
    repo_map = {
        "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.2",
        "llama-2-7b": "meta-llama/Llama-2-7b-chat-hf",
        "codellama-7b": "codellama/CodeLlama-7b-Instruct-hf"
    }
    
    repo_id = repo_map.get(model_id)
    if not repo_id:
        click.echo(f"Ошибка: Нет соответствия репозитория для {model_id}")
        return
    
    # Используем токен из параметра или из конфигурации
    hf_token = token or HUGGINGFACE_TOKEN or os.environ.get("HUGGINGFACE_TOKEN")
    
    # Проверка необходимости токена для данной модели
    requires_token = any(name in repo_id.lower() for name in ["mistral", "llama", "meta"])
    
    if not hf_token and requires_token:
        click.echo("Предупреждение: Для этой модели требуется токен Hugging Face.")
        click.echo("Пожалуйста, предоставьте токен с помощью опции --token или установите переменную окружения HUGGINGFACE_TOKEN.")
        click.echo("Вы можете получить токен на https://huggingface.co/settings/tokens")
        click.echo("\nДля создания токена с правами чтения:")
        click.echo("1. Перейдите на https://huggingface.co/settings/tokens")
        click.echo("2. Нажмите 'Новый токен'")
        click.echo("3. Введите имя для вашего токена (например, 'Code Review Bot')")
        click.echo("4. Выберите уровень доступа 'read'")
        click.echo("5. При желании установите срок действия")
        click.echo("6. Нажмите 'Сгенерировать токен' и скопируйте его")
        return
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Общие параметры для загрузки
        download_kwargs = {
            "token": hf_token,
            "revision": revision,
        }
        
        if cache_dir:
            download_kwargs["cache_dir"] = cache_dir
        
        # Загрузка токенизатора
        click.echo(f"Загрузка токенизатора из {repo_id} (ревизия: {revision})...")
        tokenizer = AutoTokenizer.from_pretrained(repo_id, **download_kwargs)
        tokenizer.save_pretrained(model_path)
        
        # Проверка наличия необходимых библиотек
        has_accelerate = False
        has_bitsandbytes_gpu = False
        
        try:
            import accelerate
            has_accelerate = True
        except ImportError:
            click.echo("Библиотека accelerate не установлена. Установите её: pip install accelerate>=0.26.0")
        
        try:
            import bitsandbytes
            # Проверка поддержки GPU в bitsandbytes
            if hasattr(bitsandbytes, "COMPILED_WITH_CUDA") and bitsandbytes.COMPILED_WITH_CUDA:
                has_bitsandbytes_gpu = True
            else:
                click.echo("Установленная версия bitsandbytes скомпилирована без поддержки GPU.")
        except ImportError:
            click.echo("Библиотека bitsandbytes не установлена.")
        
        # Загрузка модели с учетом доступных библиотек
        click.echo("Загрузка модели (это может занять некоторое время)...")
        
        # Определяем параметры загрузки модели в зависимости от доступных библиотек
        model_kwargs = download_kwargs.copy()
        
        # Если есть accelerate, можно использовать device_map
        if has_accelerate:
            model_kwargs["device_map"] = "auto"
            model_kwargs["torch_dtype"] = torch.float16
        
        # Если есть bitsandbytes с поддержкой GPU и требуется квантизация
        if model_config.get("quantization") == "4bit" and has_accelerate and has_bitsandbytes_gpu:
            from transformers import BitsAndBytesConfig
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            model_kwargs["quantization_config"] = quantization_config
            
            click.echo("Загрузка модели с 4-битной квантизацией...")
        elif model_config.get("quantization") == "4bit":
            click.echo("4-битная квантизация недоступна. Загрузка модели без квантизации...")
        
        # Загрузка модели с подготовленными параметрами
        model = AutoModelForCausalLM.from_pretrained(repo_id, **model_kwargs)
        
        model.save_pretrained(model_path)
        
        click.echo(f"Модель {model_id} успешно загружена!")
        click.echo(f"Модель сохранена в: {model_path}")
    except Exception as e:
        click.echo(f"Ошибка загрузки модели: {str(e)}")
        
        # Дополнительная информация об ошибках
        if "accelerate" in str(e).lower():
            click.echo("\nДля использования параметра device_map требуется библиотека Accelerate:")
            click.echo("pip install accelerate>=0.26.0")
        if "401" in str(e) and "Unauthorized" in str(e):
            click.echo("\nОшибка 401 Unauthorized: Ваш токен может быть недействительным или просроченным.")
            click.echo("Пожалуйста, проверьте ваш токен на https://huggingface.co/settings/tokens")
        elif "403" in str(e) and "Forbidden" in str(e) or "gated repo" in str(e):
            click.echo("\nОшибка 403 Forbidden: У вас нет доступа к этой модели.")
            click.echo("Вам необходимо принять лицензионное соглашение модели на сайте Hugging Face.")
            click.echo(f"1. Посетите: https://huggingface.co/{repo_id}")
            click.echo("2. Войдите в систему с той же учетной записью, которая сгенерировала ваш токен")
            click.echo("3. Нажмите 'Доступ к репозиторию' и примите лицензионное соглашение")
            click.echo("4. Попробуйте загрузить снова после принятия лицензии")
        elif "404" in str(e) and "Not Found" in str(e):
            click.echo("\nОшибка 404 Not Found: Репозиторий модели не найден.")
            click.echo(f"Пожалуйста, проверьте, существует ли репозиторий '{repo_id}'.")

@click.command('load-models')
@with_appcontext
def load_models_command():
    """Загрузка моделей для анализа кода."""
    from backend.services.model_service import ModelService
    
    model_service = ModelService()
    try:
        model_service._load_models()
        click.echo(f"Модели успешно загружены.")
        if hasattr(model_service, 'default_model'):
            click.echo(f"Модель по умолчанию: {model_service.default_model}")
        else:
            click.echo("Предупреждение: Модель по умолчанию не установлена.")
    except Exception as e:
        click.echo(f"Ошибка загрузки моделей: {str(e)}")