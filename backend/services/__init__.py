# Убедитесь, что сервис моделей инициализируется правильно
from backend.services.model_service import ModelService

# Создаем экземпляр сервиса моделей
model_service = ModelService()

# Загружаем модели при импорте
model_service._load_models()