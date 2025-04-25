#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Domain name
DOMAIN="gideon.lytestudios.be"
PROJECT_DIR="/home/ubuntu/discord-mods-inc"

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

# Get the actual username
ACTUAL_USER=$(who am i | awk '{print $1}')
if [ -z "$ACTUAL_USER" ]; then
    ACTUAL_USER=${SUDO_USER:-${USER}}
fi
print_status "Running setup for user: $ACTUAL_USER"

# Stop existing nginx service
print_status "Stopping existing nginx service..."
sudo systemctl stop nginx

# Generate environment file
print_status "Generating environment file..."
cat << 'EOL' | sudo tee .env > /dev/null
# Web Configuration
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_DEBUG=False
ALLOWED_HOSTS=gideon.lytestudios.be
DOMAIN=gideon.lytestudios.be

# Database settings
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=super_secret_db_password_123
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNTE2MjM5MDIyfQ.vZ7BeGD5k7RAVbXkGh-SuH9tGjhLrCuKn1W3e_Zf8tc

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# SSL settings
SSL_EMAIL=admin@lytestudios.be

# Other settings
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_key}
GITHUB_TOKEN=${GITHUB_TOKEN:-your_github_token}
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
ENCRYPTION_KEY=${ENCRYPTION_KEY:-your_encryption_key}
EOL

# Set proper permissions for .env
sudo chown $ACTUAL_USER:$ACTUAL_USER .env
sudo chmod 600 .env

# Function to install package if not present
install_if_missing() {
    if ! command -v $1 &> /dev/null; then
        print_status "Installing $1..."
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $2 || {
            print_error "Failed to install $1"
            exit 1
        }
    else
        print_status "$1 is already installed"
    fi
}

# Update package list
print_status "Updating package list..."
sudo rm -f /var/lib/apt/lists/lock
sudo rm -f /var/cache/apt/archives/lock
sudo rm -f /var/lib/dpkg/lock*
sudo dpkg --configure -a
sudo DEBIAN_FRONTEND=noninteractive apt-get update

# Install Python3 if not present
install_if_missing python3 "python3-full"
install_if_missing python3-venv "python3-venv"
install_if_missing python3-pip "python3-pip"

# Create and activate virtual environment
print_status "Setting up Python virtual environment..."
cd $PROJECT_DIR
sudo rm -rf venv
python3 -m venv venv
sudo chown -R $ACTUAL_USER:$ACTUAL_USER venv

# Install required system packages
print_status "Installing required packages..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    git \
    build-essential \
    libpq-dev

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $ACTUAL_USER
    sudo systemctl enable docker
    sudo systemctl start docker
else
    print_status "Docker is already installed"
    # Ensure user is in docker group
    sudo usermod -aG docker $ACTUAL_USER
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose is already installed"
fi

# Create necessary directories
print_status "Creating project directories..."
sudo mkdir -p /var/www/$DOMAIN/{static,media,logs,ssl,nginx/conf.d}

# Set proper permissions
print_status "Setting permissions..."
sudo chown -R $ACTUAL_USER:$ACTUAL_USER /var/www/$DOMAIN
sudo chmod -R 755 /var/www/$DOMAIN

# Configure firewall
print_status "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# Install Python dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Stop and remove any existing containers
print_status "Cleaning up existing containers..."
sudo docker-compose -f docker-compose.prod.yml down --remove-orphans

# Pull Docker images first
print_status "Pulling Docker images..."
sudo docker-compose -f docker-compose.prod.yml pull

# Build and start Docker containers
print_status "Starting Docker containers..."
sudo docker-compose -f docker-compose.prod.yml up -d --build

# Wait for web container to be ready
print_status "Waiting for web container to be ready..."
sleep 10

# Configure Nginx
print_status "Configuring Nginx..."
sudo tee /etc/nginx/conf.d/$DOMAIN.conf > /dev/null << 'EOL'
upstream django {
    server localhost:8000;
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name gideon.lytestudios.be;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gideon.lytestudios.be;

    ssl_certificate /etc/letsencrypt/live/gideon.lytestudios.be/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gideon.lytestudios.be/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

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
    access_log /var/www/gideon.lytestudios.be/logs/nginx-access.log;
    error_log /var/www/gideon.lytestudios.be/logs/nginx-error.log;

    # Proxy settings
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static/ {
        alias /var/www/gideon.lytestudios.be/static/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public";
    }

    # Media files
    location /media/ {
        alias /var/www/gideon.lytestudios.be/media/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;
    limit_req zone=one burst=10 nodelay;
}
EOL

# Obtain SSL certificate
print_status "Obtaining SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@lytestudios.be --redirect

# Setup auto-renewal for SSL
print_status "Setting up SSL auto-renewal..."
(sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -

# Copy project files
print_status "Copying project files..."
sudo cp -r web/* /var/www/$DOMAIN/
sudo cp .env /var/www/$DOMAIN/
sudo chown -R $ACTUAL_USER:$ACTUAL_USER /var/www/$DOMAIN

print_status "Setup completed successfully!"
print_warning "Please ensure you have updated the .env file with your credentials"
print_warning "Your site should be available at https://$DOMAIN"

# Reload user groups to apply docker group changes
print_warning "Please log out and back in for Docker permissions to take effect"