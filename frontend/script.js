document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.getElementById('code-input');
    const languageSelect = document.getElementById('language');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingIndicator = document.getElementById('loading');
    const resultsContainer = document.getElementById('results');
    const mlSuggestionsElement = document.getElementById('ml-suggestions');
    const staticAnalysisElement = document.getElementById('static-analysis');
    
    // API URL - проверяем доступность сервера
    const API_URL = 'http://localhost:5000/api/review';
    const PING_URL = 'http://localhost:5000/api/ping';
    
    // Проверяем доступность сервера при загрузке страницы
    async function checkServerStatus() {
        try {
            const response = await fetch(PING_URL, { method: 'GET' });
            if (response.ok) {
                console.log('Server is available');
                return true;
            } else {
                console.error('Server returned an error');
                return false;
            }
        } catch (error) {
            console.error('Cannot connect to server:', error);
            return false;
        }
    }
    
    analyzeBtn.addEventListener('click', async function() {
        const code = codeInput.value.trim();
        const language = languageSelect.value;
        
        if (!code) {
            alert('Пожалуйста, введите код для анализа');
            return;
        }
        
        // Проверяем доступность сервера перед отправкой запроса
        const serverAvailable = await checkServerStatus().catch(() => false);
        if (!serverAvailable) {
            alert('Сервер недоступен. Пожалуйста, убедитесь, что бэкенд запущен.');
            return;
        }
        
        // Показываем индикатор загрузки
        loadingIndicator.style.display = 'flex';
        resultsContainer.style.display = 'none';
        
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    language: language
                })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage;
                
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || `Ошибка сервера: ${response.status}`;
                } catch (e) {
                    errorMessage = `Ошибка сервера: ${response.status}. ${errorText}`;
                }
                
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            
            // Отображаем результаты
            mlSuggestionsElement.textContent = data.ml_suggestions || 'Нет предложений';
            
            // Форматируем результаты статического анализа
            if (data.static_analysis && data.static_analysis.length > 0) {
                let analysisHtml = '';
                
                data.static_analysis.forEach(result => {
                    analysisHtml += `<h4>${result.tool}</h4>`;
                    
                    if (!result.output) {
                        analysisHtml += `<pre>Нет данных от инструмента</pre>`;
                        return;
                    }
                    
                    try {
                        // Пытаемся распарсить JSON, если это возможно
                        const jsonOutput = JSON.parse(result.output);
                        analysisHtml += `<pre>${JSON.stringify(jsonOutput, null, 2)}</pre>`;
                    } catch (e) {
                        // Если не JSON или произошла ошибка, безопасно выводим как текст
                        // Экранируем HTML для предотвращения XSS
                        const safeOutput = result.output
                            .replace(/&/g, '&amp;')
                            .replace(/</g, '&lt;')
                            .replace(/>/g, '&gt;')
                            .replace(/"/g, '&quot;')
                            .replace(/'/g, '&#039;');
                        analysisHtml += `<pre>${safeOutput}</pre>`;
                    }
                });
                
                staticAnalysisElement.innerHTML = analysisHtml;
            } else {
                staticAnalysisElement.textContent = 'Нет результатов статического анализа';
            }
            
            // Скрываем индикатор загрузки и показываем результаты
            loadingIndicator.style.display = 'none';
            resultsContainer.style.display = 'block';
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert(`Произошла ошибка при анализе кода: ${error.message}`);
            loadingIndicator.style.display = 'none';
        }
    });
    
    // Проверяем доступность сервера при загрузке страницы
    checkServerStatus().then(available => {
        if (!available) {
            // Добавляем предупреждение на страницу
            const warning = document.createElement('div');
            warning.className = 'server-warning';
            warning.textContent = 'Внимание: Сервер анализа кода недоступен. Убедитесь, что бэкенд запущен.';
            warning.style.backgroundColor = '#fff3cd';
            warning.style.color = '#856404';
            warning.style.padding = '10px';
            warning.style.borderRadius = '4px';
            warning.style.marginBottom = '20px';
            warning.style.textAlign = 'center';
            
            document.querySelector('.code-input-section').prepend(warning);
        }
    });
});