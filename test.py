# Чтобы знать, куда загружаются модели и кэш. Особенно важно, если нужно изменить значение по-умолчанию
import os
print("TRANSFORMERS_CACHE:", os.getenv("TRANSFORMERS_CACHE"))
print("TORCH_HOME:", os.getenv("TORCH_HOME"))
print("HF_HOME:", os.getenv("HF_HOME"))