#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Domain name
DOMAIN="gideon.lytestudios.be"

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[-] $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

# Check system requirements
print_status "Checking system requirements..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is required but not installed."
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
print_status "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create necessary directories
print_status "Creating project directories..."
mkdir -p /var/www/$DOMAIN
mkdir -p /var/www/$DOMAIN/static
mkdir -p /var/www/$DOMAIN/media
mkdir -p /var/www/$DOMAIN/logs
mkdir -p /var/www/$DOMAIN/ssl
mkdir -p /var/www/$DOMAIN/nginx/conf.d

# Set proper permissions
print_status "Setting permissions..."
chown -R $SUDO_USER:$SUDO_USER /var/www/$DOMAIN
chmod -R 755 /var/www/$DOMAIN

# Configure firewall
print_status "Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

# Generate environment file if not exists
if [ ! -f .env ]; then
    print_status "Generating environment file..."
    cat > .env << EOL
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_DEBUG=False
ALLOWED_HOSTS=$DOMAIN
DOMAIN=$DOMAIN

# Database settings
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_db_password

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# SSL settings
SSL_EMAIL=your_email@example.com

# Other settings
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
EOL
    print_warning "Please edit .env file with your actual credentials"
fi

# Configure Nginx
print_status "Configuring Nginx..."
cat > /etc/nginx/conf.d/$DOMAIN.conf << EOL
upstream django {
    server web:8000;
}

map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (uncomment if you're sure)
    # add_header Strict-Transport-Security "max-age=63072000" always;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logs
    access_log /var/www/$DOMAIN/logs/nginx-access.log;
    error_log /var/www/$DOMAIN/logs/nginx-error.log;

    # Proxy settings
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static/ {
        alias /var/www/$DOMAIN/static/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public";
    }

    # Media files
    location /media/ {
        alias /var/www/$DOMAIN/media/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public";
    }

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=one:10m rate=1r/s;
    limit_req zone=one burst=10 nodelay;
}
EOL

# Obtain SSL certificate
print_status "Obtaining SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $(grep SSL_EMAIL .env | cut -d '=' -f2) --redirect

# Setup auto-renewal for SSL
print_status "Setting up SSL auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Copy project files
print_status "Copying project files..."
cp -r web/* /var/www/$DOMAIN/
cp .env /var/www/$DOMAIN/

# Build and start Docker containers
print_status "Starting Docker containers..."
docker-compose -f docker-compose.prod.yml up -d --build

print_status "Setup completed successfully!"
print_warning "Please ensure you have updated the .env file with your credentials"
print_warning "Your site should be available at https://$DOMAIN"