#!/usr/bin/env bash
set -euo pipefail

SERVER_NAME="${SERVER_NAME:-_}"
BASIC_AUTH_USER="${BASIC_AUTH_USER:-}"
BASIC_AUTH_PASS="${BASIC_AUTH_PASS:-}"

echo "Настройка Nginx..."
cp -f /opt/web_scheduler/docs/nginx.conf.example /etc/nginx/sites-available/web_scheduler
if [ "$SERVER_NAME" != "_" ]; then
  sed -i "s/server_name .*;/server_name $SERVER_NAME;/" /etc/nginx/sites-available/web_scheduler
fi
ln -sf /etc/nginx/sites-available/web_scheduler /etc/nginx/sites-enabled/web_scheduler

if [ -n "$BASIC_AUTH_USER" ] && [ -n "$BASIC_AUTH_PASS" ]; then
  echo "Обновление Basic Auth..."
  htpasswd -bc /etc/nginx/.htpasswd "$BASIC_AUTH_USER" "$BASIC_AUTH_PASS"
fi

nginx -t
systemctl reload nginx
echo "Nginx сконфигурирован."


