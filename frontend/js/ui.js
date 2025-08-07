export function showLoading() {
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('result').innerHTML = '';
    document.getElementById('result-container').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

export function hideLoading() {
    document.getElementById('loading-indicator').style.display = 'none';
}

export function displayResult(result) {
    const resultContainer = document.getElementById('result-container');
    const resultElement = document.getElementById('result');

    console.log("Displaying result:", result);
    console.log("Result type:", typeof result);

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

    try {
        console.log("Parsing markdown:", resultText);
        resultElement.innerHTML = marked.parse(resultText);
        console.log("Markdown parsed successfully");
    } catch (e) {
        console.error("Error parsing markdown:", e);
        resultElement.textContent = resultText; // Fallback to plain text
    }

    resultContainer.style.display = 'block';
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

export function displayError(message) {
    const errorElement = document.getElementById('error');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    errorElement.scrollIntoView({ behavior: 'smooth' });
}

export function updateModelSelector(data) {
    const modelSelect = document.getElementById('model-select');
    if (!modelSelect) {
        console.error("Model select element not found!");
        return;
    }

    modelSelect.innerHTML = '';

    if (data.success && data.models && Array.isArray(data.models)) {
        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            if (model.is_default || model.id === data.default_model) {
                option.selected = true;
            }
            modelSelect.appendChild(option);
        });
        console.log("Models loaded successfully");
    } else {
        console.error("Invalid models data:", data);
        const option = document.createElement('option');
        option.value = "";
        option.textContent = data.error || "Модели недоступны";
        modelSelect.appendChild(option);
    }
}

export function saveResponseLanguagePreference() {
    const responseLanguage = document.getElementById('response-language').value;
    localStorage.setItem('preferredResponseLanguage', responseLanguage);
}

export function loadResponseLanguagePreference() {
    const savedLanguage = localStorage.getItem('preferredResponseLanguage');
    if (savedLanguage) {
        document.getElementById('response-language').value = savedLanguage;
    }
}
