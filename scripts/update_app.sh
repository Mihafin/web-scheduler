#!/usr/bin/env bash
set -euo pipefail

cd /opt/web_scheduler
echo "[1/3] Обновление кода..."
git pull || true

echo "[2/3] Обновление зависимостей..."
/opt/web_scheduler/venv/bin/pip install -r requirements.txt

echo "[3/3] Обновление статики и рестарт сервиса..."
mkdir -p /var/www/web_scheduler
cp -r frontend/* /var/www/web_scheduler/ || true
systemctl restart web-scheduler
systemctl status --no-pager web-scheduler || true

echo "Обновление завершено."


