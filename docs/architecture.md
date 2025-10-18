## Архитектура системы

### Компоненты

- Клиент (SPA): React + TypeScript + FullCalendar + Tailwind CSS
  - Отрисовка календаря (Month/Week/Day), фильтры по значениям тегов, формы CRUD
  - Взаимодействует с backend через REST‑API `/api/...`

- Сервер (Backend API): FastAPI (Python) + Uvicorn
  - CRUD для расписаний, тегов и значений тегов
  - Фильтрация расписаний по интервалу дат и по списку `tag_value_ids`
  - Подключение к SQLite через SQLAlchemy

- База данных: SQLite
  - Простой файл БД, минимальные зависимости, транзакционная целостность
  - Возможность миграций через Alembic (опционально)

- Реверс‑прокси и авторизация: Nginx
  - Проксирование `/api` на Uvicorn (127.0.0.1:8000)
  - Раздача статики SPA (собранного фронтенда)
  - Basic Auth на весь сайт (микро‑аутентификация без ролей)

### Потоки данных

1. Браузер загружает SPA из Nginx
2. SPA вызывает REST‑API на `/api` (проксируется Nginx → Uvicorn → FastAPI)
3. FastAPI обращается к SQLite для чтения/записи
4. Авторизация на входе — Basic Auth в Nginx (приложение не хранит пользователей)

### Модель данных (высокоуровнево)

- `schedules (id, title, date_from, date_to)`
- `tags (id, name)`
- `tag_values (id, tag_id, value)`
- `schedule_tag_values (schedule_id, tag_value_id)`

Связи:

- `tags 1—N tag_values`
- `schedules N—M tag_values` через `schedule_tag_values`

### Нефункциональные требования

- Простота развертывания (Ubuntu + Nginx, один файл БД — SQLite)
- Предсказуемая работа при малой нагрузке (интранет/внутренний сервис)
- Возможность миграции на Postgres без изменения API


