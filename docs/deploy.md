## Деплой: Ubuntu + Nginx + SQLite + Basic Auth

### Предпосылки

- Ubuntu 22.04+/24.04
- Пакеты: `nginx`, `python3`, `python3-venv`, `git`, `sqlite3`, `apache2-utils` (для `htpasswd`)

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
pip install fastapi uvicorn[standard] sqlalchemy pydantic alembic
```

Структура приложения предполагается как `app/main.py` с объектом `app` (ASGI). При необходимости скорректируйте путь в `ExecStart` systemd‑юнита ниже.

### Инициализация базы данных

```bash
sqlite3 /opt/web_scheduler/var/data.sqlite < /opt/web_scheduler/docs/db-schema.sql
```

Убедитесь, что директория существует:

```bash
mkdir -p /opt/web_scheduler/var
```

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

### Сборка фронтенда

Если используется React + Vite:

```bash
sudo apt install -y nodejs npm
cd /opt/web_scheduler/frontend
npm ci || npm install
npm run build
sudo mkdir -p /var/www/web_scheduler
sudo cp -r dist/* /var/www/web_scheduler/
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

### Обновление

```bash
cd /opt/web_scheduler
git pull
# Пересоберите фронтенд, при необходимости перезапустите API:
sudo systemctl restart web-scheduler
```


