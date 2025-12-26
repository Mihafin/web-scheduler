## Архитектура системы

### Компоненты

- **Клиент (SPA)**: Статичные HTML/CSS/JavaScript файлы
  - Отрисовка календаря (Month/Week/Day) с помощью FullCalendar (CDN)
  - Фильтры по значениям тегов, формы CRUD
  - Взаимодействует с backend через REST-API `/api/...`
  - Журнал аудита, отчёты, управление тегами — отдельные HTML страницы

- **Сервер (Backend API)**: FastAPI (Python) + Uvicorn
  - CRUD для расписаний, тегов и значений тегов
  - Фильтрация расписаний по интервалу дат и по списку `tag_value_ids`
  - Журнал аудита всех изменений
  - Подключение к SQLite через SQLAlchemy ORM

- **База данных**: SQLite
  - Простой файл БД, минимальные зависимости, транзакционная целостность
  - Автоматические миграции при старте (через SQLAlchemy)
  - Возможность миграций через Alembic (опционально)

- **Реверс-прокси и авторизация**: Nginx
  - Проксирование `/api` на Uvicorn (127.0.0.1:8000)
  - Раздача статики SPA (HTML/CSS/JS файлов)
  - Basic Auth на весь сайт (микро-аутентификация без ролей)
  - Передача имени пользователя в заголовке `X-Remote-User`

### Технологический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Web Framework | FastAPI | 0.115.2 |
| ASGI Server | Uvicorn | 0.30.6 |
| ORM | SQLAlchemy | 2.0.35 |
| Validation | Pydantic | 2.9.2 |
| Database | SQLite | 3.x |
| Calendar UI | FullCalendar | 6.x (CDN) |
| Reverse Proxy | Nginx | 1.18+ |
| Process Manager | systemd | — |

### Потоки данных

1. Браузер загружает HTML/CSS/JS из Nginx
2. FullCalendar инициализируется и вызывает REST-API на `/api`
3. Nginx проксирует запросы → Uvicorn → FastAPI
4. FastAPI обращается к SQLite для чтения/записи
5. Авторизация на входе — Basic Auth в Nginx (приложение не хранит пользователей)
6. Имя пользователя из Basic Auth передаётся в `X-Remote-User` для журнала аудита

### Модель данных (детально)

#### Таблица `tags` — Теги

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | INTEGER PK | Уникальный идентификатор |
| name | TEXT UNIQUE | Имя тега (например, "зал", "тренер") |
| required | BOOLEAN | Обязательный тег — событие должно иметь значение |
| unique_resource | BOOLEAN | Уникальный ресурс — проверка пересечений по времени |

#### Таблица `tag_values` — Значения тегов

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | INTEGER PK | Уникальный идентификатор |
| tag_id | INTEGER FK | Ссылка на tags.id |
| value | TEXT | Значение (например, "зал1", "зал2") |
| color | TEXT NULL | HEX цвет для подсветки (#RRGGBB) |

Ограничение: UNIQUE (tag_id, value)

#### Таблица `schedules` — Расписания

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | INTEGER PK | Уникальный идентификатор |
| title | TEXT | Название события |
| date_from | TEXT | Начало события (ISO-8601) |
| date_to | TEXT | Окончание события (ISO-8601) |
| is_canceled | BOOLEAN | Признак отмены (false по умолчанию) |
| contact | TEXT NULL | Контактная информация |

Ограничение: CHECK (date_to >= date_from)

#### Таблица `schedule_tag_values` — Связь N:M

| Колонка | Тип | Описание |
|---------|-----|----------|
| schedule_id | INTEGER FK | Ссылка на schedules.id |
| tag_value_id | INTEGER FK | Ссылка на tag_values.id |

PRIMARY KEY (schedule_id, tag_value_id)

#### Таблица `audit_logs` — Журнал аудита

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | INTEGER PK | Уникальный идентификатор |
| ts | TEXT | Время операции (ISO-8601 UTC) |
| username | TEXT NULL | Имя пользователя (из X-Remote-User) |
| action | TEXT | Действие: CREATE, UPDATE, DELETE |
| entity | TEXT | Имя таблицы/сущности |
| entity_id | INTEGER NULL | ID изменённой записи |
| details | TEXT NULL | Детали изменений |

### Связи между таблицами

```
┌─────────────┐       ┌─────────────────┐       ┌──────────────┐
│   tags      │ 1───N │   tag_values    │ N───M │  schedules   │
├─────────────┤       ├─────────────────┤       ├──────────────┤
│ id          │◄──────│ tag_id          │       │ id           │
│ name        │       │ id              │◄──┐   │ title        │
│ required    │       │ value           │   │   │ date_from    │
│ unique_res. │       │ color           │   │   │ date_to      │
└─────────────┘       └─────────────────┘   │   │ is_canceled  │
                                            │   │ contact      │
                      ┌─────────────────────┤   └──────────────┘
                      │ schedule_tag_values │           │
                      ├─────────────────────┤           │
                      │ schedule_id ────────────────────┘
                      │ tag_value_id ───────┘
                      └─────────────────────┘

┌──────────────┐
│  audit_logs  │
├──────────────┤
│ id           │
│ ts           │
│ username     │
│ action       │
│ entity       │
│ entity_id    │
│ details      │
└──────────────┘
```

### Нефункциональные требования

- Простота развёртывания (Ubuntu + Nginx, один файл БД — SQLite)
- Предсказуемая работа при малой нагрузке (интранет/внутренний сервис)
- Возможность миграции на PostgreSQL без изменения API
- Полный аудит всех изменений данных

