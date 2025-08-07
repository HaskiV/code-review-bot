export function initEditor() {
    const editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        lineNumbers: true,
        mode: 'python',
        theme: 'default',
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        extraKeys: {"Tab": "indentMore", "Shift-Tab": "indentLess"}
    });
    console.log("CodeMirror initialized");
    return editor;
}
