#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Get username
USERNAME=$(whoami)
print_status "Running server setup for user: $USERNAME"

# Function to install package if not present
install_if_missing() {
    if ! command -v "$1" &> /dev/null; then
        print_status "Installing $1..."
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "$2" || {
            print_error "Failed to install $1"
            exit 1
        }
    else
        print_status "$1 is already installed"
    fi
}

# Update package list
print_status "Updating package list..."
sudo apt-get update

# Install Python3 if not present
install_if_missing python3 "python3-full"
install_if_missing python3-venv "python3-venv"
install_if_missing python3-pip "python3-pip"

# Install required system packages
print_status "Installing required packages..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    certbot \
    python3-certbot-nginx \
    ufw \
    git \
    build-essential \
    libpq-dev

# Check Docker installation
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "$USERNAME"
    sudo systemctl enable docker
    sudo systemctl start docker
else
    print_status "Docker is already installed"
    # Ensure user is in docker group
    if ! groups "$USERNAME" | grep -q "\bdocker\b"; then
        print_status "Adding user to docker group..."
        sudo usermod -aG docker "$USERNAME"
    fi
fi

# Check Docker Compose installation
print_status "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose is already installed"
fi

# Configure firewall
print_status "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

print_status "Server setup completed successfully!"
print_warning "Please log out and back in for Docker permissions to take effect"