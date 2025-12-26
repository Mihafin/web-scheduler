## Деплой: Ubuntu + Nginx + SQLite + Basic Auth

### Предпосылки

- Ubuntu 22.04+ / 24.04
- Пакеты: `nginx`, `python3`, `python3-venv`, `git`, `sqlite3`, `apache2-utils` (для `htpasswd`)

```bash
sudo apt update
sudo apt install -y nginx python3 python3-venv git sqlite3 apache2-utils
```

Опционально TLS (Let's Encrypt):

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

Скрипт сам установит пакеты, создаст venv, инициализирует SQLite, поднимет systemd-сервис и настроит Nginx (включая Basic Auth, если заданы переменные).

---

### Ручная установка

#### 1. Развёртывание кода

```bash
sudo mkdir -p /opt/web_scheduler
sudo chown -R $USER:$USER /opt/web_scheduler
cd /opt/web_scheduler
git clone <url-репозитория> .
```

#### 2. Backend (FastAPI + Uvicorn)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Текущие зависимости (requirements.txt):**

| Пакет | Версия | Назначение |
|-------|--------|------------|
| fastapi | 0.115.2 | Web framework |
| uvicorn[standard] | 0.30.6 | ASGI server |
| SQLAlchemy | 2.0.35 | ORM |
| pydantic | 2.9.2 | Валидация данных |
| python-multipart | 0.0.9 | Обработка форм |
| alembic | 1.13.3 | Миграции БД |
| jinja2 | 3.1.4 | Шаблоны |

Структура приложения предполагается как `app/main.py` с объектом `app` (ASGI). При необходимости скорректируйте путь в `ExecStart` systemd-юнита ниже.

#### 3. Инициализация базы данных

```bash
mkdir -p /opt/web_scheduler/var
sqlite3 /opt/web_scheduler/var/data.sqlite < /opt/web_scheduler/docs/db-schema.sql
```

**Примечание:** При первом запуске приложения SQLAlchemy автоматически создаст таблицы и выполнит мягкие миграции (добавит новые столбцы, если их нет).

#### 4. Systemd-юнит для API

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

#### 5. Фронтенд (без сборки)

Фронтенд — статичные HTML/JS файлы в `frontend/`, сборка не требуется. Достаточно скопировать их в директорию, которую обслуживает Nginx:

```bash
sudo mkdir -p /var/www/web_scheduler
sudo cp -r /opt/web_scheduler/frontend/* /var/www/web_scheduler/
```

#### 6. Nginx + Basic Auth

Создайте файл пользователей:

```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

Скопируйте `docs/nginx.conf.example` в `/etc/nginx/sites-available/web_scheduler` и подправьте `server_name` и пути:

```bash
sudo cp /opt/web_scheduler/docs/nginx.conf.example /etc/nginx/sites-available/web_scheduler
sudo ln -s /etc/nginx/sites-available/web_scheduler /etc/nginx/sites-enabled/web_scheduler
sudo nginx -t
sudo systemctl reload nginx
```

**Важно:** Nginx передаёт имя пользователя из Basic Auth в заголовке `X-Remote-User` для журнала аудита. См. пример в `nginx.conf.example`.

#### 7. TLS (опционально)

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

---

### Проверка

- Откройте `http://example.com` — появится запрос логина/пароля (Basic Auth)
- После входа должна загрузиться SPA; запросы `/api/...` проксируются на Uvicorn
- Проверьте журнал аудита: `/logs.html`
- Swagger UI доступен по адресу `/api/docs`

---

### Обновление

```bash
cd /opt/web_scheduler
git pull
# Обновить зависимости, статику и перезапустить сервис одной командой:
sudo bash scripts/update_app.sh
```

---

### Структура файлов на сервере

```
/opt/web_scheduler/           # Код приложения
├── app/                      # Backend
├── frontend/                 # Исходные файлы фронтенда
├── var/data.sqlite           # База данных SQLite
├── venv/                     # Python виртуальное окружение
└── ...

/var/www/web_scheduler/       # Копия статики для Nginx
├── index.html
├── tags.html
├── logs.html
└── reports.html

/etc/nginx/sites-available/   # Конфиг Nginx
└── web_scheduler

/etc/nginx/.htpasswd          # Файл паролей Basic Auth

/etc/systemd/system/          # Systemd юнит
└── web-scheduler.service
```

---

### Troubleshooting

**Сервис не запускается:**
```bash
sudo journalctl -u web-scheduler -f
```

**Ошибки Nginx:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Права на файл БД:**
```bash
sudo chown www-data:www-data /opt/web_scheduler/var/data.sqlite
sudo chmod 664 /opt/web_scheduler/var/data.sqlite
```

