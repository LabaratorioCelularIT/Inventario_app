#!/usr/bin/env bash

# Inventario App Development Launcher
# Cross-platform compatible script for Windows, Linux, and macOS

# Set script to exit on any error
set -e

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check if Docker and Docker Compose are available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed or not in PATH"
        echo "Please install Docker first:"
        echo "- Linux: https://docs.docker.com/engine/install/"
        echo "- macOS: https://docs.docker.com/desktop/mac/"
        echo "- Windows: https://docs.docker.com/desktop/windows/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "Error: Docker Compose is not available"
        echo "Please install Docker Compose or use newer Docker with built-in compose"
        exit 1
    fi
}

# Use docker compose or docker-compose based on availability
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Get the correct localhost URL based on OS
get_localhost() {
    local os=$(detect_os)
    if [[ "$os" == "linux" ]]; then
        echo "localhost"
    else
        echo "localhost"
    fi
}

# Main script starts here
clear
echo "=== Inventario App Development Environment ==="
echo "Detected OS: $(detect_os)"
echo ""

# Check dependencies
check_docker

# Get compose command
COMPOSE_CMD=$(get_compose_cmd)
LOCALHOST=$(get_localhost)

echo "Available options:"
echo "1. Start all services (legacy + new)"
echo "2. Start only new architecture (API + Frontend + MongoDB)"  
echo "3. Start only legacy applications"
echo "4. Stop all services"
echo "5. View service status"
echo "6. Reset and rebuild all containers"
echo "7. View logs"
echo "8. Clean up unused Docker resources"
echo ""

read -p "Choose an option (1-8): " choice

case $choice in
    1)
        echo "Starting all services..."
        $COMPOSE_CMD up -d
        echo ""
        echo "Services running on:"
        echo "- New React Frontend: http://$LOCALHOST:3000"
        echo "- New Flask API: http://$LOCALHOST:5000/api/v1"
        echo "- Legacy Inventory: http://$LOCALHOST:5001"
        echo "- Legacy Cash Register: http://$LOCALHOST:5003"
        echo "- Legacy Calculator: http://$LOCALHOST:5004"
        echo "- MongoDB: $LOCALHOST:27017"
        ;;
    2)
        echo "Starting new architecture only..."
        $COMPOSE_CMD up -d api frontend mongo
        echo ""
        echo "New architecture running on:"
        echo "- React Frontend: http://$LOCALHOST:3000"
        echo "- Flask API: http://$LOCALHOST:5000/api/v1"
        echo "- MongoDB: $LOCALHOST:27017"
        ;;
    3)
        echo "Starting legacy applications only..."
        $COMPOSE_CMD up -d legacy-inventario legacy-caja legacy-calculadora
        echo ""
        echo "Legacy applications running on:"
        echo "- Inventory: http://$LOCALHOST:5001"
        echo "- Cash Register: http://$LOCALHOST:5003"
        echo "- Calculator: http://$LOCALHOST:5004"
        ;;
    4)
        echo "Stopping all services..."
        $COMPOSE_CMD down
        echo "All services stopped."
        ;;
    5)
        echo "Service status:"
        $COMPOSE_CMD ps
        ;;
    6)
        echo "Resetting and rebuilding all containers..."
        $COMPOSE_CMD down -v
        $COMPOSE_CMD build --no-cache
        $COMPOSE_CMD up -d
        echo "All containers rebuilt and started."
        ;;
    7)
        echo "Available services for logs:"
        $COMPOSE_CMD ps --services
        echo ""
        read -p "Enter service name (or 'all' for all services): " service
        if [[ "$service" == "all" ]]; then
            $COMPOSE_CMD logs -f
        else
            $COMPOSE_CMD logs -f "$service"
        fi
        ;;
    8)
        echo "Cleaning up unused Docker resources..."
        docker system prune -f
        docker volume prune -f
        echo "Cleanup completed."
        ;;
    *)
        echo "Invalid option. Please choose 1-8."
        ;;
esac