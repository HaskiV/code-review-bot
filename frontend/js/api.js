import { displayResult, displayError, showLoading, hideLoading, updateModelSelector } from './ui.js';

export function loadModels() {
    console.log("Loading models...");
    fetch('/api/models')
        .then(response => {
            console.log("Models API response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Models data received:", data);
            updateModelSelector(data);
        })
        .catch(error => {
            console.error("Error loading models:", error);
            updateModelSelector({ success: false, error: 'Ошибка загрузки моделей' });
        });
}

export function analyzeCode(code, language, model, responseLanguage) {
    console.log("Analyze button clicked");
    console.log("Code:", code);
    console.log("Language:", language);
    console.log("Model:", model);
    console.log("Response Language:", responseLanguage);

    showLoading();

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
        hideLoading();
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
        hideLoading();
        console.error("Error analyzing code:", error);
        displayError(error.message);
    });
}
