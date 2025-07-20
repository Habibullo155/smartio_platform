# Использование официального образа Python в качестве базового образа
FROM python:3.11-slim-bookworm

# Установка системных зависимостей, необходимых для psycopg2-binary
# libpq-dev содержит заголовочные файлы и библиотеки для PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование файла с зависимостями в рабочую директорию
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего содержимого текущей директории в контейнер
COPY . .

# Открытие порта, на котором будет работать приложение (FastAPI по умолчанию 8000)
EXPOSE 8000

# Команда для запуска приложения
# `--host 0.0.0.0` важен для доступа к приложению извне контейнера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]