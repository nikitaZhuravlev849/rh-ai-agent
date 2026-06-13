FROM python:3.11-slim

WORKDIR /app

# Системные зависимости:
# - gcc, g++, libffi-dev, libssl-dev — для Twisted/cryptography
# - libpq-dev — для asyncpg/psycopg2
# - curl — для healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# spaCy-модель — ошибка при скачивании не ломает сборку
RUN python -m spacy download ru_core_news_sm || true

COPY . .

EXPOSE 8000
