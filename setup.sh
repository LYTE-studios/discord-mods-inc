#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Discord Mods Inc...${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

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
docker-compose build
docker-compose up -d

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Setup completed successfully!${NC}"
    echo -e "\nNext steps:"
    echo -e "1. Edit the ${YELLOW}.env${NC} file with your configuration"
    echo -e "2. Run ${YELLOW}docker-compose logs -f${NC} to view the logs"
    echo -e "3. Visit ${YELLOW}http://localhost:5000${NC} to check the application"
    echo -e "\nTo stop the application, run: ${YELLOW}docker-compose down${NC}"
else
    echo -e "\n${RED}Setup failed. Please check the error messages above.${NC}"
    exit 1
fi