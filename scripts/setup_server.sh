#!/usr/bin/env bash
set -euo pipefail

# Environment variables (override defaults via: sudo -E VAR=value bash scripts/setup_server.sh)
# REPO_URL        - Git URL репозитория (используется, если /opt/web_scheduler не содержит .git)
# SERVER_NAME     - server_name для Nginx (example.com). По умолчанию "_" (любое имя)
# BASIC_AUTH_USER - логин для Basic Auth (опционально)
# BASIC_AUTH_PASS - пароль для Basic Auth (опционально)

REPO_URL="${REPO_URL:-}"
SERVER_NAME="${SERVER_NAME:-_}"
BASIC_AUTH_USER="${BASIC_AUTH_USER:-}"
BASIC_AUTH_PASS="${BASIC_AUTH_PASS:-}"

echo "[1/7] Установка пакетов..."
apt update
apt install -y nginx python3 python3-venv git sqlite3 apache2-utils

echo "[2/7] Подготовка каталога /opt/web_scheduler..."
mkdir -p /opt/web_scheduler

if [ ! -d "/opt/web_scheduler/.git" ]; then
  if [ -n "$REPO_URL" ]; then
    echo "Клонирование репозитория: $REPO_URL"
    rm -rf /opt/web_scheduler/* || true
    git clone "$REPO_URL" /opt/web_scheduler
  else
    echo "REPO_URL не задан и репозиторий отсутствует. Задайте REPO_URL и повторите."
    exit 1
  fi
else
  echo "Репозиторий уже присутствует в /opt/web_scheduler, пропускаем клонирование."
fi

cd /opt/web_scheduler

echo "[3/7] Создание venv и установка зависимостей..."
python3 -m venv venv
/opt/web_scheduler/venv/bin/pip install --upgrade pip
/opt/web_scheduler/venv/bin/pip install -r requirements.txt

echo "[4/7] Инициализация БД SQLite..."
mkdir -p /opt/web_scheduler/var
if [ ! -f "/opt/web_scheduler/var/data.sqlite" ]; then
  sqlite3 /opt/web_scheduler/var/data.sqlite < /opt/web_scheduler/docs/db-schema.sql
else
  echo "База уже существует, пропускаем."
fi

# Права для systemd-пользователя www-data на каталог с базой данных
chown -R www-data:www-data /opt/web_scheduler/var

echo "[5/7] Настройка systemd сервиса..."
cp -f /opt/web_scheduler/docs/web-scheduler.service.example /etc/systemd/system/web-scheduler.service
systemctl daemon-reload
systemctl enable --now web-scheduler
systemctl status --no-pager web-scheduler || true

echo "[6/7] Размещение статического фронтенда..."
mkdir -p /var/www/web_scheduler
cp -r /opt/web_scheduler/frontend/* /var/www/web_scheduler/ || true

echo "[7/7] Настройка Nginx и Basic Auth..."
cp -f /opt/web_scheduler/docs/nginx.conf.example /etc/nginx/sites-available/web_scheduler
if [ "$SERVER_NAME" != "_" ]; then
  sed -i "s/server_name .*;/server_name $SERVER_NAME;/" /etc/nginx/sites-available/web_scheduler
fi
ln -sf /etc/nginx/sites-available/web_scheduler /etc/nginx/sites-enabled/web_scheduler

if [ -n "$BASIC_AUTH_USER" ] && [ -n "$BASIC_AUTH_PASS" ]; then
  htpasswd -bc /etc/nginx/.htpasswd "$BASIC_AUTH_USER" "$BASIC_AUTH_PASS"
else
  echo "BASIC_AUTH_USER/BASIC_AUTH_PASS не заданы — Basic Auth не обновлялся."
fi

nginx -t
systemctl reload nginx

echo "Готово. Проверьте http://$SERVER_NAME (или IP), API проксируется на /api/."


