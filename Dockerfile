FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для данных
RUN mkdir -p /app/data

# Переменные окружения
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/bot.db

# Порт
EXPOSE 8000

# Запуск бота
CMD ["python", "bot.py"]
