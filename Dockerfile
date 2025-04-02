FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY frontend/ ./static/

# Устанавливаем необходимые инструменты для статического анализа
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && npm install -g eslint \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5000

CMD ["python", "app.py"]