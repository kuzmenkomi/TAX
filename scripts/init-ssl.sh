#!/bin/sh

# init-ssl.sh
# Handles the chicken-and-egg problem of Nginx and SSL certificates.

set -e

DOMAIN=${DOMAIN:-localhost}
EMAIL=${ADMIN_EMAIL:-admin@example.com}
SSL_PATH="/etc/nginx/ssl/live/$DOMAIN"

if [ -f "$SSL_PATH/fullchain.pem" ]; then
    echo "✅ SSL certificate already exists for $DOMAIN. Skipping initialization."
    exit 0
fi

echo "🚀 Initializing dummy SSL certificate for $DOMAIN..."

mkdir -p "$SSL_PATH"

# Generate dummy self-signed certificate
openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout "$SSL_PATH/privkey.pem" \
    -out "$SSL_PATH/fullchain.pem" \
    -subj "/CN=localhost"

echo "✅ Dummy certificate generated. Nginx can now start and Certbot can perform challenges."
