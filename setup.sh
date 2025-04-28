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

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

# Stop existing nginx service
print_status "Stopping existing nginx service..."
sudo systemctl stop nginx || true
sudo systemctl disable nginx || true

# Generate environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Generating environment file..."
    cat > .env << 'EOL'
# Web Configuration
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DJANGO_DEBUG=False
ALLOWED_HOSTS=gideon.lytestudios.be
DOMAIN=gideon.lytestudios.be

# Database settings
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password_123
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# SSL settings
SSL_EMAIL=admin@lytestudios.be

# Other settings
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
ENCRYPTION_KEY=your_encryption_key
EOL

    chmod 600 .env
fi

# Create necessary directories
print_status "Creating project directories..."
sudo mkdir -p "/var/www/$DOMAIN"/{static,media,logs}
sudo chown -R "$USERNAME:$USERNAME" "/var/www/$DOMAIN"

# Set up Django project structure
print_status "Setting up Django project structure..."
mkdir -p web/{config,chat,users,templates,static}
mkdir -p web/templates/{chat,users}
mkdir -p web/static/{css,js}

# Copy existing modules to Django project
cp -r ai web/ai
cp -r cogs web/cogs
cp -r monitoring web/monitoring
cp -r security web/security
cp -r tickets web/tickets
cp -r utils web/utils
cp -r workflow web/workflow

# Copy requirements.txt
cp requirements.txt web/

# Stop and remove any existing containers
print_status "Cleaning up existing containers..."
docker compose down --remove-orphans

# Build and start Docker containers
print_status "Starting Docker containers..."
docker compose up -d --build

# Wait for web container to be ready
print_status "Waiting for web container to be ready..."
sleep 10

# Copy project files
print_status "Copying project files..."
sudo cp -r web/* "/var/www/$DOMAIN/"
sudo cp .env "/var/www/$DOMAIN/"
sudo chown -R "$USERNAME:$USERNAME" "/var/www/$DOMAIN"

print_status "Setup completed successfully!"
print_warning "Please ensure you have:"
print_warning "1. Updated the .env file with your credentials"
print_warning "2. Set up DNS records for $DOMAIN pointing to this server"
print_warning "3. Once DNS is propagated, run: sudo certbot --nginx -d $DOMAIN"
print_warning "Your site is available at http://$DOMAIN"
print_warning "After DNS propagation, run certbot to enable HTTPS"