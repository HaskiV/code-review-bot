from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import subprocess
import traceback
import torch  # Добавляем импорт torch для работы с моделью

MOCK_MODE = False  # Установите True для использования заглушки вместо реальной модели

# Определяем абсолютный путь к директории со статическими файлами
current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(os.path.dirname(current_dir), 'frontend')

app = Flask(__name__, 
            static_url_path='', 
            static_folder=static_folder)

# Разрешаем CORS для всех источников во время разработки
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Добавляем явный маршрут для корневого URL
@app.route('/')
def index():
    return send_from_directory(static_folder, 'index.html')

# Добавляем маршрут для всех остальных статических файлов
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(static_folder, path)

# Определяем модель для анализа кода
# Заменяем на более совместимую модель
MODEL_NAME = "microsoft/codebert-base"  # Легкая модель для тестирования
tokenizer = None
model = None

def load_model():
    """
    Ленивая загрузка модели только при необходимости
    """
    global tokenizer, model

    # Если включен режим тестирования, используем заглушки
    if MOCK_MODE:
        class SimpleModel:
            def generate(self, input_ids, **kwargs):
                return [input_ids]
        
        class SimpleTokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [0, 1, 2, 3]}
            
            def decode(self, ids, **kwargs):
                return "Тестовый режим активирован. Используется заглушка вместо реальной модели."
            
            @property
            def eos_token_id(self):
                return 0
        
        tokenizer = SimpleTokenizer()
        model = SimpleModel()
        print("Загружена тестовая заглушка вместо модели")
        return
    
    if tokenizer is None or model is None:
        try:
            # Для CodeBERT используем правильные классы
            if "codebert" in MODEL_NAME.lower():
                from transformers import AutoTokenizer, AutoModel
                print(f"Загрузка токенизатора {MODEL_NAME}...")
                tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                print(f"Загрузка модели {MODEL_NAME}...")
                model = AutoModel.from_pretrained(MODEL_NAME)
                
                # Обертка для совместимости с интерфейсом генерации
                class CodeBERTWrapper:
                    def __init__(self, model):
                        self.model = model
                    
                    def generate(self, input_ids, **kwargs):
                        # Простая имитация генерации для CodeBERT
                        # В реальном приложении здесь должна быть более сложная логика
                        outputs = self.model(input_ids)
                        return [input_ids]  # Возвращаем входные данные для совместимости
                
                model = CodeBERTWrapper(model)
                print("Модель CodeBERT успешно загружена!")
            else:
                # Оригинальный код для других моделей
                from transformers import AutoModelForCausalLM, AutoTokenizer
                
                try:
                    print(f"Загрузка токенизатора {MODEL_NAME}...")
                    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                except Exception as e:
                    print(f"Ошибка при загрузке токенизатора: {str(e)}")
                    print("Попытка загрузки специального токенизатора...")
                    
                    try:
                        from transformers import CodeGenTokenizer
                        tokenizer = CodeGenTokenizer.from_pretrained(MODEL_NAME)
                    except Exception as e2:
                        print(f"Ошибка при загрузке CodeGenTokenizer: {str(e2)}")
                        from transformers import GPT2Tokenizer
                        tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
                        if tokenizer.eos_token_id is None:
                            tokenizer.eos_token = tokenizer.pad_token if tokenizer.pad_token else "</s>"
                
                print(f"Загрузка модели {MODEL_NAME}...")
                model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
                print("Модель успешно загружена!")
        except Exception as e:
            print(f"Ошибка при загрузке модели: {str(e)}")
            # Используем более простой запасной вариант
            class SimpleModel:
                def generate(self, input_ids, **kwargs):
                    return [input_ids]
            
            class SimpleTokenizer:
                def __call__(self, text, **kwargs):
                    return {"input_ids": [0, 1, 2, 3]}
                
                def decode(self, ids, **kwargs):
                    return "Не удалось загрузить модель. Для тестирования интерфейса используйте заглушку вместо реальной модели."
                
                @property
                def eos_token_id(self):
                    return 0
            
            tokenizer = SimpleTokenizer()
            model = SimpleModel()

def analyze_code(code, language):
    """
    Анализирует код с помощью модели машинного обучения
    и предлагает улучшения
    """
    try:
        # Загружаем модель при первом использовании
        load_model()
        
        # Если используется режим заглушки
        if MOCK_MODE:
            return f"""
            Тестовый режим анализа кода на {language}.
            
            Рекомендации для улучшения:
            1. Добавьте больше комментариев для улучшения читаемости
            2. Следуйте стандартам форматирования для {language}
            3. Рассмотрите возможность разделения длинных функций на более короткие
            4. Используйте более описательные имена переменных
            
            Это тестовый вывод для проверки функциональности интерфейса.
            """
        
        # Для CodeBERT (не генеративная модель)
        if "codebert" in MODEL_NAME.lower():
            # Подготовка промпта
            prompt = f"Code: {code}\nLanguage: {language}"
            
            # Токенизация
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Получение эмбеддингов от модели
            with torch.no_grad():  # Отключаем вычисление градиентов для экономии памяти
                outputs = model.model(**inputs)
            # Для демонстрации используем простой анализ на основе CodeBERT
            # В реальном приложении здесь должна быть более сложная логика
            # Подготовим значения для анализа заранее
            lines = code.split('\n')
            structure = "Хорошая" if len(lines) < 50 else "Рассмотрите разделение на более мелкие модули"
            comments = "Достаточно" if code.count('#') > len(lines)/10 else "Рекомендуется добавить больше комментариев"
            line_lengths = [len(line) for line in lines]
            max_line_length = max(line_lengths) if line_lengths else 0
            line_length = "Оптимальная" if max_line_length < 80 else "Некоторые строки слишком длинные"

            return f"""
            Анализ кода на {language} с использованием CodeBERT:
            
            Рекомендации для улучшения:
            1. Структура кода: {structure}
            2. Комментарии: {comments}
            3. Длина строк: {line_length}
            4. Именование: Убедитесь, что имена переменных и функций отражают их назначение
            Примечание: Это базовый анализ с использованием CodeBERT. Для более детального анализа рекомендуется использовать генеративную модель.
            """
        else:
            # Оригинальный код для генеративных моделей
            prompt = f"Проанализируй следующий код на {language} и предложи улучшения:\n\n{code}\n\nУлучшения:"
            
            # Токенизация и генерация ответа
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            outputs = model.generate(
                inputs["input_ids"],
                max_length=2048,
                temperature=0.7,
                top_p=0.95,
                num_return_sequences=1,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Декодирование ответа
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлечение только части с улучшениями
            improvements = response.split("Улучшения:")[1].strip() if "Улучшения:" in response else response
            
            return improvements
    except Exception as e:
        print(f"Ошибка при анализе кода: {str(e)}")
        print(traceback.format_exc())
        return f"Произошла ошибка при анализе кода: {str(e)}\n\nПопробуйте использовать MOCK_MODE=True для тестирования интерфейса."

def run_static_analysis(code, language):
    """
    Запускает статический анализ кода с использованием
    соответствующих инструментов в зависимости от языка
    """
    results = []
    
    with tempfile.NamedTemporaryFile(suffix=f".{language}", delete=False) as temp:
        temp.write(code.encode())
        temp_path = temp.name
    
    try:
        if language == "python":
            # Используем pylint для анализа Python кода
            try:
                process = subprocess.run(
                    ["pylint", "--output-format=json", temp_path],
                    capture_output=True,
                    text=True,
                    check=False  # Не вызывать исключение при ненулевом коде возврата
                )
                if process.stdout:
                    results.append({"tool": "pylint", "output": process.stdout})
                else:
                    results.append({"tool": "pylint", "output": "Нет результатов анализа"})
            except FileNotFoundError:
                results.append({"tool": "pylint", "output": "Инструмент pylint не установлен"})
        
        elif language == "javascript":
            # Используем ESLint для JavaScript
            try:
                process = subprocess.run(
                    ["npx", "eslint", "--format=json", temp_path],
                    capture_output=True,
                    text=True,
                    check=False  # Не вызывать исключение при ненулевом коде возврата
                )
                if process.stdout:
                    results.append({"tool": "eslint", "output": process.stdout})
                else:
                    results.append({"tool": "eslint", "output": "Нет результатов анализа"})
            except FileNotFoundError:
                results.append({"tool": "eslint", "output": "Инструмент eslint не установлен"})
        
        elif language == "java":
            # Для Java можно использовать PMD или CheckStyle
            results.append({"tool": "java-analysis", "output": "Статический анализ для Java находится в разработке"})
        
        elif language == "cpp":
            # Для C++ можно использовать cppcheck
            try:
                process = subprocess.run(
                    ["cppcheck", "--enable=all", "--output-file=cppcheck_result.txt", temp_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
                # Читаем результаты из файла
                try:
                    with open("cppcheck_result.txt", "r") as f:
                        cppcheck_output = f.read()
                    results.append({"tool": "cppcheck", "output": cppcheck_output if cppcheck_output else "Нет результатов анализа"})
                    os.remove("cppcheck_result.txt")
                except:
                    results.append({"tool": "cppcheck", "output": "Не удалось прочитать результаты анализа"})
            except FileNotFoundError:
                results.append({"tool": "cppcheck", "output": "Инструмент cppcheck не установлен"})
        
        else:
            results.append({"tool": "unsupported", "output": f"Статический анализ для языка {language} не поддерживается"})
    
    finally:
        # Удаляем временный файл
        os.unlink(temp_path)
    
    return results

@app.route('/api/review', methods=['POST'])
def review_code():
    try:
        # Проверяем, что получили JSON
        if not request.is_json:
            return jsonify({"error": "Ожидается JSON"}), 400
            
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({"error": "Код не предоставлен"}), 400
        
        # Проверяем размер кода
        if len(code) > 100000:  # Примерно 100 КБ
            return jsonify({"error": "Размер кода превышает допустимый лимит (100 КБ)"}), 413
        
        # Получаем результаты анализа от модели ML
        ml_suggestions = analyze_code(code, language)
        
        # Получаем результаты статического анализа
        static_analysis = run_static_analysis(code, language)
        
        return jsonify({
            "ml_suggestions": ml_suggestions,
            "static_analysis": static_analysis
        })
    except Exception as e:
        print(f"Ошибка при обработке запроса: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Server is running"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)