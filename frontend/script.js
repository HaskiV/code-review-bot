// Отладочные сообщения
console.log("Script loaded");

// Глобальные переменные
let editor;

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded");
    
    // Инициализация CodeMirror
    editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        lineNumbers: true,
        mode: 'python',
        theme: 'default',
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        extraKeys: {"Tab": "indentMore", "Shift-Tab": "indentLess"}
    });
    console.log("CodeMirror initialized");
    
    // Загрузка моделей
    loadModels();
    
    // Загрузка сохраненных настроек
    loadResponseLanguagePreference();
    
    // Обработчик события изменения языка программирования
    document.getElementById('language-select').addEventListener('change', function() {
        const language = this.value;
        editor.setOption('mode', language);
    });
    
    // Обработчик события изменения языка ответа
    document.getElementById('response-language').addEventListener('change', saveResponseLanguagePreference);
    
    // Обработчик события нажатия на кнопку анализа
    document.getElementById('analyze-button').addEventListener('click', analyzeCode);
    console.log("Analyze button event listener added");
});

// Загрузка списка моделей с сервера
function loadModels() {
    console.log("Loading models...");
    
    // Отправляем запрос на получение списка моделей
    fetch('/api/models')
        .then(response => {
            console.log("Models API response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Models data received:", data);
            
            // Получаем элемент select для моделей
            const modelSelect = document.getElementById('model-select');
            if (!modelSelect) {
                console.error("Model select element not found!");
                return;
            }
            
            // Очищаем текущие опции
            modelSelect.innerHTML = '';
            
            // Проверяем, что данные корректны
            if (data.success && data.models && Array.isArray(data.models)) {
                // Добавляем опции для каждой модели
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    
                    // Устанавливаем модель по умолчанию
                    if (model.is_default || model.id === data.default_model) {
                        option.selected = true;
                    }
                    
                    modelSelect.appendChild(option);
                });
                
                console.log("Models loaded successfully");
            } else {
                console.error("Invalid models data:", data);
                
                // Добавляем опцию-заглушку
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "Модели недоступны";
                modelSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error("Error loading models:", error);
            
            // Получаем элемент select для моделей
            const modelSelect = document.getElementById('model-select');
            if (modelSelect) {
                // Очищаем текущие опции
                modelSelect.innerHTML = '';
                
                // Добавляем опцию-заглушку
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "Ошибка загрузки моделей";
                modelSelect.appendChild(option);
            }
        });
}

// Анализ кода
function analyzeCode() {
    const code = editor.getValue();
    const language = document.getElementById('language-select').value;
    const model = document.getElementById('model-select').value;
    const responseLanguage = document.getElementById('response-language').value;
    
    console.log("Analyze button clicked");
    console.log("Code:", code);
    console.log("Language:", language);
    console.log("Model:", model);
    console.log("Response Language:", responseLanguage);
    
    // Показываем индикатор загрузки
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('result').innerHTML = '';
    document.getElementById('result-container').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    
    fetch('/api/review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            code: code,
            language: language,
            model: model,
            response_language: responseLanguage
        })
    })
    .then(response => {
        console.log("Review API response status:", response.status);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(`Ошибка сервера: ${response.status}${data.error ? ' - ' + data.error : ''}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Скрываем индикатор загрузки
        document.getElementById('loading-indicator').style.display = 'none';
        
        console.log("API response data:", data);
        
        if (data.success) {
            console.log("Success, displaying result");
            displayResult(data.result);
        } else {
            console.error("API returned error:", data.error);
            throw new Error(data.error || 'Неизвестная ошибка');
        }
    })
    .catch(error => {
        // Скрываем индикатор загрузки
        document.getElementById('loading-indicator').style.display = 'none';
        
        console.error("Error analyzing code:", error);
        displayError(error.message);
    });
}

// Отображение результата анализа
function displayResult(result) {
    const resultContainer = document.getElementById('result-container');
    const resultElement = document.getElementById('result');
    
    console.log("Displaying result:", result);
    console.log("Result type:", typeof result);
    
    // Проверяем тип результата и преобразуем его в строку, если это объект
    let resultText = result;
    if (typeof result === 'object') {
        try {
            resultText = JSON.stringify(result, null, 2);
            console.log("Converted object to string:", resultText);
        } catch (e) {
            console.error("Error stringifying result:", e);
            resultText = "Ошибка преобразования результата: " + e.message;
        }
    }
    
    // Преобразуем markdown в HTML
    try {
        console.log("Parsing markdown:", resultText);
        resultElement.innerHTML = marked.parse(resultText);
        console.log("Markdown parsed successfully");
    } catch (e) {
        console.error("Error parsing markdown:", e);
        resultElement.textContent = resultText; // Fallback to plain text
    }
    
    // Показываем контейнер с результатами
    resultContainer.style.display = 'block';
    
    // Прокручиваем страницу к результатам
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

// Отображение ошибки
function displayError(message) {
    const errorElement = document.getElementById('error');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    // Прокручиваем страницу к сообщению об ошибке
    errorElement.scrollIntoView({ behavior: 'smooth' });
}

// Сохранение выбранного языка ответа в localStorage
function saveResponseLanguagePreference() {
    const responseLanguage = document.getElementById('response-language').value;
    localStorage.setItem('preferredResponseLanguage', responseLanguage);
}

// Загрузка сохраненного языка ответа при загрузке страницы
function loadResponseLanguagePreference() {
    const savedLanguage = localStorage.getItem('preferredResponseLanguage');
    if (savedLanguage) {
        document.getElementById('response-language').value = savedLanguage;
    }
}