#!/bin/bash

# Inventario App Development Launcher
# This script helps start different parts of the application

# Detect which compose command to use
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "ERROR: Neither 'docker compose' nor 'docker-compose' is available"
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

echo "=== Inventario App Development Environment ==="
echo "Using: $COMPOSE_CMD"
echo ""
echo "Available options:"
echo "1. Start all services (legacy + new)"
echo "2. Start only new architecture (API + Frontend + MongoDB)"  
echo "3. Start only legacy applications"
echo "4. Stop all services"
echo "5. View service status"
echo "6. Reset and rebuild all containers"
echo "7. View logs (all services)"
echo "8. View logs (specific service)"
echo ""

read -p "Choose an option (1-8): " choice

case $choice in
    1)
        echo "Starting all services..."
        $COMPOSE_CMD up -d
        echo ""
        echo "Services running on:"
        echo "- New React Frontend: http://localhost:3000"
        echo "- New Flask API: http://localhost:5000/api/v1"
        echo "- Legacy Inventory: http://localhost:5001"
        echo "- Legacy Cash Register: http://localhost:5003"
        echo "- Legacy Calculator: http://localhost:5004"
        echo "- MongoDB: localhost:27017"
        ;;
    2)
        echo "Starting new architecture only..."
        $COMPOSE_CMD up -d api frontend mongo
        echo ""
        echo "New architecture running on:"
        echo "- React Frontend: http://localhost:3000"
        echo "- Flask API: http://localhost:5000/api/v1"
        echo "- MongoDB: localhost:27017"
        ;;
    3)
        echo "Starting legacy applications only..."
        $COMPOSE_CMD up -d legacy-inventario legacy-caja legacy-calculadora
        echo ""
        echo "Legacy applications running on:"
        echo "- Inventory: http://localhost:5001"
        echo "- Cash Register: http://localhost:5003"
        echo "- Calculator: http://localhost:5004"
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
        echo "Viewing logs for all services..."
        $COMPOSE_CMD logs -f
        ;;
    8)
        echo "Available services:"
        $COMPOSE_CMD ps --services
        echo ""
        read -p "Enter service name: " service
        echo "Viewing logs for $service (Press Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f "$service"
        ;;
    *)
        echo "Invalid option. Please choose 1-8."
        ;;
esac