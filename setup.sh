#!/bin/bash

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Domain name
DOMAIN="gideon.lytestudios.be"
PROJECT_DIR="/home/ubuntu/discord-mods-inc"
USERNAME=$(whoami)

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "An error occurred during setup"
        print_status "Cleaning up..."
        docker compose down --remove-orphans 2>/dev/null || true
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Function to print status messages
print_status() {
    echo "${GREEN}[+] $1${NC}"
}

print_warning() {
    echo "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo "${RED}[-] $1${NC}"
}

# Check for required tools
check_requirements() {
    # Check Docker
    if ! docker --version &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose (try both new and legacy versions)
    if ! (docker compose version &> /dev/null || docker-compose --version &> /dev/null); then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check rsync
    if ! rsync --version &> /dev/null; then
        print_error "rsync is not installed. Please install rsync first."
        exit 1
    fi
    
    # Verify Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start the Docker service."
        exit 1
    fi
}

# Generate and validate environment file
setup_env() {
    if [ ! -f .env ]; then
        print_status "Generating environment file..."
        # Generate secrets
        DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
        JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
        ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        
        cat > .env << EOL
# Web Configuration
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
DJANGO_DEBUG=False
ALLOWED_HOSTS=gideon.lytestudios.be
DOMAIN=gideon.lytestudios.be

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=discord_mods
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_database_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Security Configuration
ENCRYPTION_KEY=${ENCRYPTION_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# SSL Configuration
SSL_EMAIL=hello@lytestudios.be

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=bot.log
EOL
        chmod 600 .env
    fi

    # Validate required environment variables
    print_status "Validating environment variables..."
    required_vars=(
        "DJANGO_SECRET_KEY"
        "ALLOWED_HOSTS"
        "REDIS_HOST"
        "REDIS_PORT"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_HOST"
    )
    missing_vars=()
    
    while IFS= read -r line; do
        if [[ $line =~ ^[^#]*= ]]; then
            key=$(echo "$line" | cut -d'=' -f1)
            value=$(echo "$line" | cut -d'=' -f2-)
            if [[ " ${required_vars[@]} " =~ " ${key} " ]] && [[ -z "$value" ]]; then
                missing_vars+=("$key")
            fi
        fi
    done < .env

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
}

# Set up error handling
set -e

# Check requirements first
print_status "Checking system requirements..."
check_requirements

# Setup and validate environment
setup_env

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    print_status "Creating project directory..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R "$USERNAME:$USERNAME" "$PROJECT_DIR"
fi

# Stop existing nginx service
print_status "Stopping existing nginx service..."
sudo systemctl stop nginx || true
sudo systemctl disable nginx || true

# Function to install and configure certbot
setup_ssl() {
    print_status "Setting up SSL..."
    
    # Install certbot and nginx plugin
    if ! command -v certbot &> /dev/null; then
        print_status "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi

    # Ensure nginx is not running
    docker compose stop nginx

    # Get SSL certificate
    if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        print_status "Obtaining SSL certificate..."
        certbot certonly --standalone \
            --non-interactive \
            --agree-tos \
            --email "$SSL_EMAIL" \
            --domains "$DOMAIN" \
            --preferred-challenges http

        if [ $? -ne 0 ]; then
            print_error "Failed to obtain SSL certificate"
            exit 1
        fi
    else
        print_warning "SSL certificate already exists"
    fi

    # Create SSL directory in Docker volume
    print_status "Setting up SSL certificates for nginx..."
    docker volume create discord-mods-inc_certs

    # Copy certificates to Docker volume
    docker run --rm \
        -v discord-mods-inc_certs:/certs \
        -v /etc/letsencrypt:/etc/letsencrypt:ro \
        alpine sh -c "mkdir -p /certs && cp -rL /etc/letsencrypt/live/$DOMAIN/* /certs/"

    # Set up auto-renewal
    print_status "Setting up auto-renewal..."
    cat > /etc/cron.weekly/renew-cert << EOF
#!/bin/bash
certbot renew --quiet
docker compose restart nginx
EOF
    chmod +x /etc/cron.weekly/renew-cert

    # Start nginx
    docker compose up -d nginx
}

# Create necessary directories
print_status "Creating project directories..."
if [ ! -d "/var/www/$DOMAIN" ]; then
    sudo mkdir -p "/var/www/$DOMAIN"/{static,media,logs}
    sudo chown -R "$USERNAME:$USERNAME" "/var/www/$DOMAIN"
else
    print_warning "Directory /var/www/$DOMAIN already exists, skipping creation"
fi

# Set up Django project structure
print_status "Setting up Django project structure..."
# First ensure core directory exists
if [ ! -d "web/core" ]; then
    print_error "web/core directory not found! This is required for the project."
    exit 1
fi

# Create other required directories
mkdir -p web/{config,chat,users,templates,static,staticfiles,media}
mkdir -p web/templates/{chat,users}
mkdir -p web/static/{css,js}

# Set proper permissions for static and media directories
print_status "Setting up static and media directories..."
sudo chown -R "$USERNAME:$USERNAME" web/static web/staticfiles web/media
sudo chmod -R 777 web/static web/staticfiles web/media

# Core modules check already done above

# Copy requirements.txt
cp requirements.txt web/

# Check requirements before Docker operations
check_requirements

# Stop and remove any existing containers
print_status "Cleaning up existing containers..."
docker compose down --remove-orphans

# Create Docker volumes with proper permissions
print_status "Creating Docker volumes..."
docker volume rm discord-mods-inc_static_volume discord-mods-inc_media_volume discord-mods-inc_certs || true
docker volume create discord-mods-inc_static_volume
docker volume create discord-mods-inc_media_volume
docker volume create discord-mods-inc_certs

# Set up SSL certificates
setup_ssl

# Build and start Docker containers
print_status "Building and starting containers..."
if ! docker compose up -d --build; then
    print_error "Failed to start containers"
    docker compose logs
    exit 1
fi

# Monitor container startup
print_status "Monitoring container startup..."
attempt=1
max_attempts=30
while [ $attempt -le $max_attempts ]; do
    if docker compose ps | grep -q "unhealthy\|exit"; then
        print_error "Container health check failed"
        docker compose logs
        exit 1
    fi
    
    if docker compose ps | grep -q "running\|healthy"; then
        print_status "All containers are running"
        break
    fi
    
    echo "Waiting for containers to be ready... ($attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    print_error "Containers failed to start in time"
    docker compose logs
    exit 1
fi

# Wait for web container to be ready
print_status "Waiting for web container to be ready..."
sleep 10

# Copy project files
print_status "Copying project files..."
sudo rsync -av --delete web/ "/var/www/$DOMAIN/"
sudo cp .env "/var/www/$DOMAIN/"
sudo chown -R "$USERNAME:$USERNAME" "/var/www/$DOMAIN"
sudo chmod 755 "/var/www/$DOMAIN"

# Set up SSL certificates
setup_ssl

print_status "Setup completed successfully!"
print_warning "Please ensure you have:"
print_warning "1. Updated the .env file with your credentials"
print_warning "2. Verified DNS records for $DOMAIN are pointing to this server"
print_warning "Your site is available at https://$DOMAIN"