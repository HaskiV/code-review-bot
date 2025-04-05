import os
import torch
from typing import Dict, Any, Optional

class LocalModelService:
    """Сервис для работы с локальными LLM-моделями."""
    
    def __init__(self):
        self.loaded_models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Используемое устройство: {self.device}")
    
    def load_model(self, model_id: str) -> bool:
        """Загрузка локальной модели."""
        from backend.config.model_config import LOCAL_MODELS, get_local_model_path
        
        if model_id in self.loaded_models:
            return True
        
        model_config = LOCAL_MODELS.get(model_id)
        if not model_config:
            print(f"Модель {model_id} не найдена в конфигурации")
            return False
        
        model_path = get_local_model_path(model_id)
        if not os.path.exists(model_path):
            print(f"Путь к модели не найден: {model_path}")
            return False
        
        try:
            print(f"Загрузка модели {model_id} из {model_path}...")
            
            model_type = model_config.get("type", "").lower()
            quantization = model_config.get("quantization")
            
            if model_type in ["llama", "codellama"]:
                self._load_llama_model(model_id, model_path, quantization)
            elif model_type == "mistral":
                self._load_mistral_model(model_id, model_path, quantization)
            else:
                print(f"Неподдерживаемый тип модели: {model_type}")
                return False
            
            print(f"Модель {model_id} успешно загружена")
            return True
        except Exception as e:
            print(f"Ошибка загрузки модели {model_id}: {str(e)}")
            return False
    
    def _load_llama_model(self, model_id: str, model_path: str, quantization: Optional[str] = None):
        """Загрузка модели Llama/CodeLlama."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Настройка квантизации для экономии памяти
        if quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
        else:
            quantization_config = None
        
        # Загрузка токенизатора и модели
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        self.loaded_models[model_id] = {
            "model": model,
            "tokenizer": tokenizer
        }
    
    def _load_mistral_model(self, model_id: str, model_path: str, quantization: Optional[str] = None):
        """Загрузка модели Mistral."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Настройка квантизации для экономии памяти
        if quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
        else:
            quantization_config = None
        
        # Загрузка токенизатора и модели
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
        self.loaded_models[model_id] = {
            "model": model,
            "tokenizer": tokenizer
        }
    
    def analyze_code(self, model_id: str, code: str, language: str) -> Dict[str, Any]:
        """Анализ кода с использованием локальной модели."""
        if model_id not in self.loaded_models:
            success = self.load_model(model_id)
            if not success:
                raise ValueError(f"Не удалось загрузить модель {model_id}")
        
        model_data = self.loaded_models[model_id]
        model = model_data["model"]
        tokenizer = model_data["tokenizer"]
        
        # Формирование промпта для анализа кода
        prompt = f"""Проанализируйте следующий код на языке {language} и предложите улучшения:

```{language}
{code}
```"""

        # Генерация ответа
        inputs = tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Извлечение только ответа модели (без промпта)
        response = response[len(prompt):].strip()
        
        # Парсинг ответа в структурированный формат
        analysis = self._parse_response(response)
        
        return {
            "model": model_id,
            "analysis": analysis
        }
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа модели в структурированный формат."""
        sections = {
            "Code Quality": [],
            "Bugs": [],
            "Performance": [],
            "Security": [],
            "Best Practices": []
        }
        current_section = None
        
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # Определение секции
            if "code quality" in line.lower():
                current_section = "Code Quality"
                continue
            elif "bugs" in line.lower() or "potential bugs" in line.lower():
                current_section = "Bugs"
                continue
            elif "performance" in line.lower():
                current_section = "Performance"
                continue
            elif "security" in line.lower():
                current_section = "Security"
                continue
            elif "best practices" in line.lower():
                current_section = "Best Practices"
                continue
            
            # Добавление пункта в текущую секцию
            if current_section and line.startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5.")):
                clean_line = line.lstrip("-*•123456789. ").strip()
                if clean_line:
                    sections[current_section].append(clean_line)
        
        return sections
    