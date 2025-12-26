# Web Scheduler — документация проекта

## Цели

- Предоставить веб-интерфейс в стиле Google Calendar для работы с расписаниями
- Возможность фильтрации расписаний по значениям тегов (например, «зал1», «зал2»)
- CRUD-операции для всех сущностей: расписания, теги, значения тегов
- Аудит всех изменений (журнал действий)
- Простейшая авторизация при доступе к сайту через Nginx (Basic Auth)
- Развёртывание на Ubuntu, веб-сервер Nginx, база данных SQLite (минимальная зависимость)

## Основные сущности и связи

- **Расписание** (`schedules`): заголовок, дата/время "с" и "по", признак отмены, контактная информация
- **Тег** (`tags`): имя, флаги: `required` (обязательный), `unique_resource` (уникальный ресурс — контроль пересечений)
- **Значение тега** (`tag_values`): принадлежит тегу (например, «зал1», «зал2»), поле `color` (HEX)
- **Связь N—M** между расписаниями и значениями тегов (`schedule_tag_values`)
- **Журнал аудита** (`audit_logs`): фиксирует все CREATE/UPDATE/DELETE операции
- **Клиенты** (`clients`): справочник клиентов (id, имя)
- **Типы абонементов** (`subscription_types`): шаблоны абонементов (название, кол-во занятий, срок в днях)
- **Покупки абонементов** (`subscription_purchases`): записи о покупке абонементов клиентами
- **Расходы абонементов** (`subscription_expenses`): записи об использовании занятий

Схема отношений:

- Один `tag` имеет много `tag_values`
- Одно `schedule` имеет много `tag_values` через таблицу `schedule_tag_values`
- Один `tag_value` может относиться ко многим `schedule`

## Выбранные технологии

### Backend (API)
- **Python 3.10+**
- **FastAPI 0.115.2** — ASGI web framework
- **Uvicorn 0.30.6** — ASGI сервер
- **SQLAlchemy 2.0.35** — ORM для работы с БД
- **Pydantic 2.9.2** — валидация данных и сериализация
- **Alembic 1.13.3** — миграции БД (опционально)
- **Jinja2 3.1.4** — шаблонизатор
- **python-multipart 0.0.9** — обработка multipart форм

### Frontend (UI)
- **HTML/CSS/JavaScript** — статичные файлы, без сборки
- **FullCalendar 6.x** — библиотека календаря (подключается через CDN)
- **CSS** — стилизация без фреймворков (кастомные стили)

### База данных
- **SQLite** — файловая БД, минимальные зависимости

### Инфраструктура
- **Nginx** — реверс-прокси, раздача статики, Basic Auth
- **systemd** — управление сервисом на сервере

## Архитектура

См. `docs/architecture.md`.

## Модель данных

SQL-схема и индексы: `docs/db-schema.sql`.

## API

Спецификация REST-эндпоинтов: `docs/api.md`.

## Интерфейс (UI)

Описание экранов, фильтров и форм CRUD: `docs/ui.md`.
Ключевые моменты:
- Фильтры: мультивыбор значений; «Основной тег для подсветки» — селект
- Цвета: задаются на уровне значений тегов и используются для подсветки событий
- Мобильная панель и drawer для фильтров; без общего скролла страницы
- В модалке событий есть «Скопировать…» с вариантами (завтра/недели), с пред-проверкой конфликтов
- Отмена событий (is_canceled) — перечёркнутый стиль вместо удаления
- Контактная информация для событий

## Деплой

Пошаговый гайд для Ubuntu + Nginx + Basic Auth: `docs/deploy.md` (включая пример `docs/nginx.conf.example`).

## Минимальные функциональные требования к первой версии (MVP)

1. Просмотр расписаний в режиме месяц/неделя/день
2. Фильтрация по значениям тегов (мультивыбор)
3. Создание/редактирование/удаление расписаний, тегов и значений тегов
4. Отмена событий без удаления (isCanceled)
5. Журнал изменений (аудит)
6. Доступ к сайту защищён Nginx Basic Auth

## Запуск локально (dev)

1. Создать и активировать venv, установить зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Инициализировать БД:

```bash
mkdir -p var
sqlite3 var/data.sqlite < docs/db-schema.sql
```

3. Запустить API:

```bash
venv/bin/uvicorn app.main:app --reload --port 8000
```

4. Открыть `http://localhost:8000` для доступа к UI или `http://localhost:8000/docs` для Swagger UI.

## Структура проекта

```
web_scheduler/
├── app/                    # Backend (FastAPI)
│   ├── main.py             # Точка входа ASGI приложения
│   ├── db.py               # Подключение к БД, сессии
│   ├── models.py           # SQLAlchemy модели
│   ├── schemas.py          # Pydantic схемы
│   ├── utils.py            # Вспомогательные функции (аудит)
│   └── routers/            # API роутеры
│       ├── health.py       # GET /api/health
│       ├── tags.py         # CRUD /api/tags
│       ├── tag_values.py   # CRUD /api/tags/{id}/values
│       ├── schedules.py    # CRUD /api/schedules
│       ├── audit.py        # GET /api/audit
│       ├── clients.py      # CRUD /api/clients
│       ├── subscription_types.py  # CRUD /api/subscription-types
│       └── subscriptions.py       # Покупки/расходы /api/subscriptions
├── frontend/               # Статичные HTML/CSS/JS файлы
│   ├── index.html          # Основной интерфейс календаря
│   ├── tags.html           # Управление тегами
│   ├── logs.html           # Журнал аудита
│   ├── reports.html        # Отчёты
│   ├── clients.html        # Управление клиентами
│   ├── subscriptions.html  # Абонементы (покупки и расходы)
│   └── subscription_types.html  # Типы абонементов (шаблоны)
├── docs/                   # Документация
│   ├── api.md              # Описание API
│   ├── architecture.md     # Архитектура системы
│   ├── db-schema.sql       # SQL-схема БД
│   ├── deploy.md           # Инструкции по деплою
│   ├── ui.md               # Описание UI
│   └── nginx.conf.example  # Пример конфига Nginx
├── scripts/                # Скрипты автоматизации
│   ├── setup_server.sh     # Первоначальная настройка сервера
│   ├── update_app.sh       # Обновление приложения
│   └── nginx_setup.sh      # Настройка Nginx
├── var/                    # Данные (БД)
│   └── data.sqlite         # Файл SQLite базы
├── requirements.txt        # Python зависимости
├── Dockerfile              # Docker образ (опционально)
└── README.md               # Этот файл
```

