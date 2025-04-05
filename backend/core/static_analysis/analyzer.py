import os
import tempfile
import subprocess
import json
from typing import List, Dict, Any

def run_static_analysis(code: str, language: str) -> List[Dict[str, Any]]:
    """
    Запускает статический анализ кода с использованием
    соответствующих инструментов в зависимости от языка
    
    Args:
        code: Исходный код для анализа
        language: Язык программирования
        
    Returns:
        Список результатов анализа
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