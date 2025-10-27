## Деплой: Ubuntu + Nginx + Cloud SQL (PostgreSQL) + Basic Auth

### Предпосылки

- Ubuntu 22.04+/24.04
- Пакеты: `nginx`, `python3`, `python3-venv`, `git`, `apache2-utils` (для `htpasswd`)

```bash
sudo apt update
sudo apt install -y nginx python3 python3-venv git sqlite3 apache2-utils
```

Опционально TLS:

```bash
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### Быстрый старт (скриптом)

```bash
# На сервере под пользователем с sudo
sudo mkdir -p /opt/web_scheduler && sudo chown -R $USER:$USER /opt/web_scheduler
cd /opt/web_scheduler
git clone <url-репозитория> .

# Запуск автоматизированной установки:
sudo -E SERVER_NAME=example.com BASIC_AUTH_USER=admin BASIC_AUTH_PASS='strongpass' bash scripts/setup_server.sh
```

Скрипт сам установит пакеты, создаст venv, поднимет systemd‑сервис и настроит Nginx (включая Basic Auth, если заданы переменные). Для работы приложения обязательно задайте `DATABASE_URL` (PostgreSQL/Cloud SQL).

### Ручная установка

### Развёртывание кода

```bash
sudo mkdir -p /opt/web_scheduler
sudo chown -R $USER:$USER /opt/web_scheduler
cd /opt/web_scheduler
git clone <url-репозитория> .
```

### Backend (FastAPI + Uvicorn)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn[standard] sqlalchemy pydantic alembic psycopg2-binary
```

Структура приложения предполагается как `app/main.py` с объектом `app` (ASGI). При необходимости скорректируйте путь в `ExecStart` systemd‑юнита ниже.

### Настройка базы данных

Приложение читает DSN из переменной окружения `DATABASE_URL` (обязательно). Фолбэка на SQLite нет.

Поддерживаемые схемы URL:

- PostgreSQL (Cloud SQL PostgreSQL):
  - `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME`
  - Через Unix‑сокет (Cloud SQL Proxy/Connector): `postgresql+psycopg2://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE`

Параметры пула можно настраивать переменными:

- `DB_POOL_SIZE` (по умолчанию 5)
- `DB_MAX_OVERFLOW` (по умолчанию 10)
- `DB_POOL_RECYCLE` (секунды, по умолчанию 1800)
- `DB_POOL_PRE_PING` (true/false, по умолчанию true)

### Systemd‑юнит для API

Создайте файл `/etc/systemd/system/web-scheduler.service`:

```ini
[Unit]
Description=Web Scheduler API (Uvicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/web_scheduler
Environment=PYTHONUNBUFFERED=1
# Установите строку подключения к Cloud SQL (пример для PostgreSQL через Unix‑сокет)
# Environment=DATABASE_URL=postgresql+psycopg2://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE
# Настроить пул при желании:
# Environment=DB_POOL_SIZE=5
# Environment=DB_MAX_OVERFLOW=10
# Environment=DB_POOL_RECYCLE=1800
# Environment=DB_POOL_PRE_PING=true
ExecStart=/opt/web_scheduler/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now web-scheduler
sudo systemctl status web-scheduler
```

### Фронтенд (без сборки)

В текущей версии фронтенд — статичные HTML/JS файлы в `frontend/`, сборка не требуется. Достаточно скопировать их в директорию, которую обслуживает Nginx:

```bash
sudo mkdir -p /var/www/web_scheduler
sudo cp -r /opt/web_scheduler/frontend/* /var/www/web_scheduler/
```

### Nginx + Basic Auth

Создайте файл пользователей:

```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

Скопируйте `docs/nginx.conf.example` в `/etc/nginx/sites-available/web_scheduler` и подправьте `server_name` и пути:

```bash
sudo ln -s /etc/nginx/sites-available/web_scheduler /etc/nginx/sites-enabled/web_scheduler
sudo nginx -t
sudo systemctl reload nginx
```

### TLS (опционально)

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

### Проверка

- Откройте `http://example.com` — появится запрос логина/пароля (Basic Auth)
- После входа должна загрузиться SPA; запросы `/api/...` проксируются на Uvicorn

### Подключение к Cloud SQL

Варианты:

- Через публичный IP инстанса Cloud SQL (брандмауэр, SSL по необходимости): используйте `HOST:PORT` напрямую в `DATABASE_URL`.
- Через Unix‑сокет `/cloudsql/PROJECT:REGION:INSTANCE` на GCE/GKE/Cloud Run (или с установленным Cloud SQL Proxy/Connector): используйте URL‑параметр `host` (PostgreSQL).

Примеры `DATABASE_URL`:

- PostgreSQL (сокет):
  `postgresql+psycopg2://app_user:strongpass@/webscheduler?host=/cloudsql/myproj:us-central1:scheduler`

- PostgreSQL (IP):
  `postgresql+psycopg2://app_user:strongpass@10.0.0.12:5432/webscheduler`

Инициализация схемы: выполните SQL из `docs/db-schema.sql` в целевой БД.
Для Postgres:

```bash
psql "postgresql://USER:PASSWORD@HOST:PORT/DBNAME" -f /opt/web_scheduler/docs/db-schema.sql
```

```

### Обновление

```bash
cd /opt/web_scheduler
git pull
# Обновить зависимости, статику и перезапустить сервис одной командой:
sudo bash scripts/update_app.sh
```


