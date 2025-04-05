@app.route('/api/review', methods=['POST'])
def review_code():
    """
    Обработка запроса на анализ кода.
    """
    try:
        # Получаем данные из запроса
        print(f"Request content type: {request.content_type}")
        print(f"Request data: {request.data}")
        
        # Пробуем разные способы получения данных
        try:
            data = request.json
            print(f"Parsed JSON data: {data}")
        except Exception as json_error:
            print(f"Error parsing JSON: {str(json_error)}")
            # Пробуем получить данные из формы
            data = request.form.to_dict()
            print(f"Form data: {data}")
            if not data:
                # Пробуем получить данные из raw body
                try:
                    import json
                    data = json.loads(request.data.decode('utf-8'))
                    print(f"Parsed raw data: {data}")
                except Exception as raw_error:
                    print(f"Error parsing raw data: {str(raw_error)}")
        
        if not data:
            print("Error: No request data")
            return jsonify({"error": "Отсутствуют данные запроса"}), 400
        
        # Проверяем наличие необходимых полей
        required_fields = ['code', 'language']
        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field: {field}")
                return jsonify({"error": f"Отсутствует обязательное поле: {field}"}), 400
        
        # Получаем код и язык программирования
        code = data['code']
        language = data['language']
        model_id = data.get('model', get_default_model_id())
        
        print(f"Processing request: language={language}, model={model_id}, code length={len(code)}")
        
        # Проверяем длину кода
        max_code_length = int(get_env_variable("MAX_CODE_LENGTH", "10000"))
        if len(code) > max_code_length:
            print(f"Error: Code exceeds maximum length ({len(code)} > {max_code_length})")
            return jsonify({
                "error": f"Код превышает максимально допустимую длину ({max_code_length} символов)"
            }), 400
        
        # Остальной код остается без изменений
        # Анализируем код с помощью выбранной модели
        print(f"Analyzing code with model: {model_id}")
        try:
            # Создаем модель для анализа
            model = create_model(model_id)
            
            # Анализируем код
            result = model.analyze_code(code, language)
            
            # Возвращаем результат
            return jsonify({
                "result": result,
                "model": model_id
            })
        except Exception as e:
            print(f"Error analyzing code with {model_id}: {str(e)}")
            
            # Если указанная модель недоступна, используем запасную модель
            fallback_model_id = "mock-model"
            print(f"Falling back to {fallback_model_id}")
            
            fallback_model = create_model(fallback_model_id)
            result = fallback_model.analyze_code(code, language)
            
            return jsonify({
                "result": result,
                "model": fallback_model_id,
                "warning": f"Произошла ошибка при использовании модели {model_id}. Использована запасная модель."
            })
    
    except Exception as e:
        print(f"Error in review_code: {str(e)}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500