#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$HOME/VCEWMarksheet}"
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
ENV_FILE="$APP_DIR/.env.production"
NGINX_SITE="/etc/nginx/sites-available/ai-marks"

command -v docker >/dev/null || { echo "Docker is required" >&2; exit 1; }
command -v nginx >/dev/null || { echo "Nginx is required" >&2; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required" >&2; exit 1; }

wait_for_url() {
  local url="$1"
  for _ in {1..30}; do
    curl -fsS "$url" >/dev/null && return 0
    sleep 2
  done
  echo "Health check failed: $url" >&2
  return 1
}

cd "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  db_password="$(openssl rand -hex 24)"
  secret_key="$(openssl rand -hex 48)"
  cat >"$ENV_FILE" <<EOF
APP_ENV=production
APP_NAME=VCEW Marksheet System
SECRET_KEY=$secret_key
DATABASE_URL=postgresql+psycopg://marksheets:$db_password@postgres:5432/marksheets
POSTGRES_PASSWORD=$db_password
ALLOWED_ORIGINS=["https://marksheet.dhinadts.com"]
DOCUMENT_STORAGE_PATH=/app/storage
DOCUMENT_STORAGE_BACKEND=local
EOF
  echo "Created $ENV_FILE with restricted permissions"
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend alembic upgrade head

wait_for_url http://127.0.0.1:8000/health
wait_for_url http://127.0.0.1:3000/

sudo tee "$NGINX_SITE" >/dev/null <<'NGINX'
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    listen [::]:80;
    server_name marksheet.dhinadts.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name marksheet.dhinadts.com;

    ssl_certificate /etc/letsencrypt/live/marksheet.dhinadts.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marksheet.dhinadts.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
NGINX

sudo ln -sfn "$NGINX_SITE" /etc/nginx/sites-enabled/ai-marks

# api.dhinadts.com is owned by the existing dhinadts site. Point that upstream
# at this backend while avoiding a duplicate server_name in ai-marks.
sudo sed -i 's#proxy_pass http://127\.0\.0\.1:3001;#proxy_pass http://127.0.0.1:8000;#g' \
  /etc/nginx/sites-available/dhinadts

sudo nginx -t
sudo systemctl reload nginx

wait_for_url https://api.dhinadts.com/health
wait_for_url https://marksheet.dhinadts.com/
echo "Deployment successful: https://marksheet.dhinadts.com and https://api.dhinadts.com"
