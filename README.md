# RH AI Agent — ПроКомпетенции

ИИ-агент для автоматического поиска партнёров проектного обучения в УрФУ.

## Архитектура

```
rh-ai-agent/
├── backend/                   # FastAPI + PostgreSQL + Celery
│   └── app/
│       ├── models/            # SQLAlchemy модели БД
│       ├── schemas/           # Pydantic схемы
│       ├── services/          # Бизнес-логика
│       │   ├── hh_parser.py   # Парсинг HH.ru и Superjob
│       │   ├── nlp_service.py # NLP извлечение компетенций
│       │   ├── company_scorer.py # Скоринг компаний (0-100)
│       │   ├── llm_service.py # Claude — генерация писем и ТЗ
│       │   ├── email_service.py  # SendGrid рассылки
│       │   └── memory_service.py # Память агента
│       ├── api/v1/            # REST API роуты
│       │   ├── industry.py    # Фаза 1: анализ компетенций
│       │   ├── companies.py   # Фаза 2: поиск и скоринг
│       │   ├── communications.py # Фазы 3-4: outreach
│       │   ├── projects.py    # Фаза 5: каталог проектов
│       │   └── dashboard.py   # Дашборд и KPI
│       └── tasks/             # Celery задачи
│           ├── outreach_tasks.py # Авто-рассылка и фоллоу-апы
│           └── parsing_tasks.py  # Парсинг вакансий и компаний
└── frontend/                  # React + Vite + Tailwind
    └── src/
        ├── pages/             # Dashboard, Companies, Communications, Projects
        └── api/               # API клиент
```

## Фазы работы агента

| # | Фаза | Автономно | Эскалация |
|---|------|-----------|-----------|
| 1 | Анализ индустрии и компетенций | Парсинг HH/Superjob + NLP | Утверждение приоритетной отрасли |
| 2 | Поиск и скоринг компаний | Сбор 100+ компаний, скоринг 0-100 | Верификация шорт-листа |
| 3 | Генерация коммуникаций | LLM-генерация персонализированных писем | Утверждение текстов |
| 4 | Outreach | Авто-рассылка + фоллоу-апы (7/14 дней) | Положительный ответ → передача человеку |
| 5 | Сбор проектов | Генерация ТЗ + структурирование ролей | Автономно |

## Запуск через Docker

```bash
cp backend/.env.example backend/.env
# Заполните API ключи в backend/.env

docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## Локальный запуск

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m spacy download ru_core_news_sm
uvicorn app.main:app --reload

# Celery worker (отдельный терминал)
celery -A app.tasks.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

## Настройка API ключей

В `backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...    # Claude для генерации писем
HH_API_TOKEN=...                # HH.ru (опционально, работает и без)
SUPERJOB_API_KEY=...            # Superjob API
SENDGRID_API_KEY=SG...          # Email рассылки
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/rh_ai_agent
REDIS_URL=redis://localhost:6379/0
```

## KPI проекта

- **KPI-1**: 100+ потенциальных партнёров за 1 месяц
- **KPI-2**: Отклик на письма > 15%
- **KPI-3**: 10+ партнёрских соглашений за семестр
- **KPI-4**: 20+ проектов в каталоге
- **KPI-5**: Сокращение времени поиска с 2 мес. до 2 недель
