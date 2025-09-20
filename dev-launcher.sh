#!/bin/bash

# Inventario App Development Launcher
# This script helps start different parts of the application

echo "=== Inventario App Development Environment ==="
echo ""
echo "Available options:"
echo "1. Start all services (legacy + new)"
echo "2. Start only new architecture (API + Frontend + MongoDB)"  
echo "3. Start only legacy applications"
echo "4. Stop all services"
echo "5. View service status"
echo "6. Reset and rebuild all containers"
echo ""

read -p "Choose an option (1-6): " choice

case $choice in
    1)
        echo "Starting all services..."
        docker-compose up -d
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
        docker-compose up -d api frontend mongo
        echo ""
        echo "New architecture running on:"
        echo "- React Frontend: http://localhost:3000"
        echo "- Flask API: http://localhost:5000/api/v1"
        echo "- MongoDB: localhost:27017"
        ;;
    3)
        echo "Starting legacy applications only..."
        docker-compose up -d legacy-inventario legacy-caja legacy-calculadora
        echo ""
        echo "Legacy applications running on:"
        echo "- Inventory: http://localhost:5001"
        echo "- Cash Register: http://localhost:5003"
        echo "- Calculator: http://localhost:5004"
        ;;
    4)
        echo "Stopping all services..."
        docker-compose down
        echo "All services stopped."
        ;;
    5)
        echo "Service status:"
        docker-compose ps
        ;;
    6)
        echo "Resetting and rebuilding all containers..."
        docker-compose down -v
        docker-compose build --no-cache
        docker-compose up -d
        echo "All containers rebuilt and started."
        ;;
    *)
        echo "Invalid option. Please choose 1-6."
        ;;
esac