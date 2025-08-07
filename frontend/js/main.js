import { loadModels, analyzeCode } from './api.js';
import { initEditor } from './editor.js';
import { loadResponseLanguagePreference, saveResponseLanguagePreference } from './ui.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded");

    const editor = initEditor();

    loadModels();
    loadResponseLanguagePreference();

    document.getElementById('language-select').addEventListener('change', function() {
        const language = this.value;
        editor.setOption('mode', language);
    });

    document.getElementById('response-language').addEventListener('change', saveResponseLanguagePreference);

    document.getElementById('analyze-button').addEventListener('click', () => {
        const code = editor.getValue();
        const language = document.getElementById('language-select').value;
        const model = document.getElementById('model-select').value;
        const responseLanguage = document.getElementById('response-language').value;
        analyzeCode(code, language, model, responseLanguage);
    });
    console.log("Analyze button event listener added");
});
