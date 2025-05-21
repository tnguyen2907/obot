#!/bin/bash

set -euo pipefail

# Log all output
exec > >(tee -a /var/log/startup-script.log) 2>&1
echo "[$(date)] Starting setup script"

# Install required packages
echo "[$(date)] Installing required packages"
apt-get update
apt-get install -y docker.io cron jq

systemctl enable --now docker
systemctl enable --now cron

# Create directories
mkdir -p /etc/letsencrypt /var/lib/letsencrypt /var/log/letsencrypt
mkdir -p /usr/share/nginx/html

# Create custom error pages
echo "<html><body><h1>404 - Page Not Found</h1></body></html>" > /usr/share/nginx/html/404.html
echo "<html><body><h1>Server Error</h1></body></html>" > /usr/share/nginx/html/50x.html

# Docker
echo "[$(date)] Authenticating to Artifact Registry"
TOKEN=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
  | jq -r .access_token)

echo $TOKEN | docker login -u oauth2accesstoken --password-stdin ${region}-docker.pkg.dev

docker network create app-network || true

echo "[$(date)] Pulling and running app containers"

IMAGE="${region}-docker.pkg.dev/${gcp_project_id}/obot-${env}/chatbot:in-use"
echo "[$(date)] Will run image: $IMAGE"

docker pull $IMAGE
docker run -d --restart=always --name chatbot --network app-network $IMAGE

# Get SSL certificates (one-time setup)
if [ "${env}" = "dev" ]; then
  DOMAINS="dev.obiebot.com www.dev.obiebot.com"
else
  DOMAINS="obiebot.com www.obiebot.com"
fi

for DOMAIN in $DOMAINS; do
  echo "[$(date)] Obtaining SSL certificate for $DOMAIN"
  docker run --rm --name certbot \
    --network host \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    -v /var/log/letsencrypt:/var/log/letsencrypt \
    certbot/certbot certonly \
      --standalone --preferred-challenges http \
      --non-interactive --agree-tos --no-eff-email \
      -d "$DOMAIN"
done

# Nginx
echo "[$(date)] Pulling Nginx images"
docker pull nginx:alpine

# Create Nginx config file
echo "[$(date)] Creating Nginx configuration"
mkdir -p /etc/nginx/conf.d

# Common HTTP block (ACME + redirect)
cat > /etc/nginx/conf.d/default.conf <<'EOF'
# Redirect HTTP to HTTPS, but serve ACME challenges
server {
    listen 80;
    listen [::]:80;
    server_name obiebot.com www.obiebot.com dev.obiebot.com www.dev.obiebot.com;

    # ACME HTTP-01 challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files \$uri =404;
    }

    # All other HTTP → HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

if [ "${env}" = "prod" ]; then
  cat >> /etc/nginx/conf.d/default.conf <<'EOF'
# Production HTTPS
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name obiebot.com www.obiebot.com;

    ssl_certificate     /etc/letsencrypt/live/obiebot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/obiebot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://chatbot:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

else
  cat >> /etc/nginx/conf.d/default.conf <<'EOF'
# Development HTTPS
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name dev.obiebot.com www.dev.obiebot.com;

    ssl_certificate     /etc/letsencrypt/live/dev.obiebot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dev.obiebot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://chatbot:8502;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
fi


# Create directory for certbot challenges
mkdir -p /var/www/certbot

# Run NGINX with the config
echo "[$(date)] Starting Nginx"
docker run -d --restart=always --name nginx-proxy -p 80:80 -p 443:443 --network app-network \
  -v /etc/nginx/conf.d:/etc/nginx/conf.d \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  -v /var/www/certbot:/var/www/certbot \
  -v /usr/share/nginx/html:/usr/share/nginx/html \
  nginx:alpine


# Setup renewal cron job
echo "[$(date)] Setting up cron job for certificate renewal"
(crontab -l 2>/dev/null || echo "") | grep -v certbot | { cat; echo "0 3 * * * docker run --rm --name certbot \
  --network host \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  -v /var/log/letsencrypt:/var/log/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot renew --webroot -w /var/www/certbot --quiet && \
  docker exec nginx-proxy nginx -s reload"; } | crontab -

echo "[$(date)] Setup complete!"