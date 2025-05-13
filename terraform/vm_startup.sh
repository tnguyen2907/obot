#!/bin/bash

# Log all output
exec > >(tee -a /var/log/startup-script.log) 2>&1
echo "[$(date)] Starting setup script"

# Install required packages
echo "[$(date)] Installing required packages"
apt-get update
apt-get install -y docker.io cron docker-credential-gcr

systemctl enable --now docker
systemctl enable --now cron

# Create directories
mkdir -p /etc/letsencrypt
mkdir -p /var/lib/letsencrypt
mkdir -p /var/log/letsencrypt
mkdir -p /usr/share/nginx/html

# Create custom error pages
echo "<html><body><h1>404 - Page Not Found</h1></body></html>" > /usr/share/nginx/html/404.html
echo "<html><body><h1>Server Error</h1></body></html>" > /usr/share/nginx/html/50x.html

# Docker
echo "[$(date)] Authenticating to Artifact Registry"
docker-credential-gcr configure-docker   # automatic Artifact Registry auth

docker network create app-network || true

echo "[$(date)] Pulling and running app containers"

IMAGE="${region}-docker.pkg.dev/${gcp_project_id}/obot-${env}/chatbot:in-use"
echo "[$(date)] Will run image: ${IMAGE}"

docker pull $IMAGE
docker run -d --restart=always --name chatbot --network app-network $IMAGE

# Pull Nginx and Certbot
echo "[$(date)] Pulling Nginx and Certbot images"
docker pull nginx:alpine
docker pull certbot/certbot

# Create Nginx config file
echo "[$(date)] Creating Nginx configuration"
mkdir -p /etc/nginx/conf.d
cat > /etc/nginx/conf.d/default.conf <<'NGINXCONF'
# Redirect HTTP traffic for all domains to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name obiebot.com www.obiebot.com dev.obiebot.com www.dev.obiebot.com;

    # For certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Handle HTTPS traffic for obiebot.com and www.obiebot.com
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name obiebot.com www.obiebot.com;

    ssl_certificate /etc/letsencrypt/live/obiebot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/obiebot.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;

    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # Location for custom error pages
    location = /404.html {
        root /usr/share/nginx/html;
    }

    location = /50x.html {
        root /usr/share/nginx/html;
    }

    # Proxy requests to the backend service
    location / {
        proxy_pass http://chatbot:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Handle HTTPS traffic for dev.obiebot.com and www.dev.obiebot.com
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name dev.obiebot.com www.dev.obiebot.com;

    ssl_certificate /etc/letsencrypt/live/dev.obiebot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dev.obiebot.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;

    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # Location for custom error pages
    location = /404.html {
        root /usr/share/nginx/html;
    }

    location = /50x.html {
        root /usr/share/nginx/html;
    }

    # Proxy requests to the dev backend service
    location / {
        proxy_pass http://chatbot:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXCONF

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

# Initial certificate setup with Certbot
echo "[$(date)] Setting up initial SSL certificates"
docker run --rm --name certbot \
  --network host \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  -v /var/log/letsencrypt:/var/log/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  --email your-email@example.com --agree-tos --no-eff-email \
  -d obiebot.com -d www.obiebot.com -d dev.obiebot.com -d www.dev.obiebot.com

# Reload NGINX to apply SSL certificates
docker exec nginx-proxy nginx -s reload 

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