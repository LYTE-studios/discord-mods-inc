#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Discord Mods Inc...${NC}\n"

# Function to check if we're running on Ubuntu/Debian
is_ubuntu_debian() {
    [ -f "/etc/debian_version" ]
}

# Function to check if we're running on RHEL/CentOS/Fedora
is_rhel_based() {
    [ -f "/etc/redhat-release" ]
}

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed successfully!${NC}"
}

# Function to install Docker on RHEL/CentOS/Fedora
install_docker_rhel() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    sudo dnf -y install dnf-plugins-core
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed successfully!${NC}"
}

# Function to install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
}

# Check and install Docker if needed
if ! command -v docker &> /dev/null; then
    if is_ubuntu_debian; then
        install_docker_ubuntu
    elif is_rhel_based; then
        install_docker_rhel
    else
        echo -e "${RED}Unsupported operating system. Please install Docker manually.${NC}"
        exit 1
    fi
fi

# Check and install Docker Compose if needed
if ! command -v docker-compose &> /dev/null; then
    install_docker_compose
fi

# Install Python dependencies if needed
if is_ubuntu_debian; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-full pipenv
elif is_rhel_based; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    sudo dnf install -y python3 python3-pip pipenv
fi

# Setup Python environment with pipenv
echo -e "${YELLOW}Setting up Python environment with pipenv...${NC}"
if ! command -v pipenv &> /dev/null; then
    sudo pip3 install pipenv
fi

# Initialize pipenv and install dependencies
export PIPENV_VENV_IN_PROJECT=1  # Keep virtualenv in project directory
pipenv --python 3
pipenv lock  # Generate new Pipfile.lock
pipenv install --deploy  # Install from Pipfile.lock
pipenv install --dev --deploy  # Install dev dependencies from Pipfile.lock

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please edit it with your configuration.${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs data

# Set correct permissions
echo -e "${YELLOW}Setting correct permissions...${NC}"
chmod +x setup.sh
chmod 600 .env

# Build and start containers
echo -e "${YELLOW}Building and starting Docker containers...${NC}"
sudo docker-compose build
sudo docker-compose up -d

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Setup completed successfully!${NC}"
    echo -e "\nNext steps:"
    echo -e "1. Edit the ${YELLOW}.env${NC} file with your configuration"
    echo -e "2. Run ${YELLOW}sudo docker-compose logs -f${NC} to view the logs"
    echo -e "3. Visit ${YELLOW}http://localhost:5000${NC} to check the application"
    echo -e "\nTo stop the application, run: ${YELLOW}sudo docker-compose down${NC}"
    echo -e "\nTo activate the Python environment, run: ${YELLOW}pipenv shell${NC}"
    
    # Notify about Docker group
    if [ -n "$(groups | grep docker)" ]; then
        echo -e "\n${YELLOW}Note: You've been added to the docker group. Please log out and back in for this to take effect.${NC}"
    fi
else
    echo -e "\n${RED}Setup failed. Please check the error messages above.${NC}"
    exit 1
fi