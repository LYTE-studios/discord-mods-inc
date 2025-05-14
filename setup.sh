#!/usr/bin/env bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then
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

# Check for required tools
check_requirements() {
    # Check Docker
    if ! which docker &> /dev/null && ! test -x "/usr/bin/docker"; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! which docker-compose &> /dev/null && ! which "docker compose" &> /dev/null && ! test -x "/usr/bin/docker-compose"; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check rsync
    if ! which rsync &> /dev/null && ! test -x "/usr/bin/rsync"; then
        print_error "rsync is not installed. Please install rsync first."
        exit 1
    fi
    
    # Verify Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start the Docker service."
        exit 1
    fi
}

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

# Set up error handling
set -e

# Check requirements first
print_status "Checking system requirements..."
check_requirements

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
mkdir -p web/{config,chat,users,templates,static}
mkdir -p web/templates/{chat,users}
mkdir -p web/static/{css,js}

# Core modules check already done above

# Copy requirements.txt
cp requirements.txt web/

# Check requirements before Docker operations
check_requirements

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
sudo rsync -av --delete web/ "/var/www/$DOMAIN/"
sudo cp .env "/var/www/$DOMAIN/"
sudo chown -R "$USERNAME:$USERNAME" "/var/www/$DOMAIN"
sudo chmod 755 "/var/www/$DOMAIN"

print_status "Setup completed successfully!"
print_warning "Please ensure you have:"
print_warning "1. Updated the .env file with your credentials"
print_warning "2. Set up DNS records for $DOMAIN pointing to this server"
print_warning "3. Once DNS is propagated, run: sudo certbot --nginx -d $DOMAIN"
print_warning "Your site is available at http://$DOMAIN"
print_warning "After DNS propagation, run certbot to enable HTTPS"