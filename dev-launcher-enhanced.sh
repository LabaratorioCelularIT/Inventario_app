#!/bin/bash

# Inventario App Development Launcher - Enhanced Version
# Supports both Docker and Terminal execution modes

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

# Detect operating system
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    elif [ "$(uname)" = "Darwin" ]; then
        echo "macos"
    elif [ "$(uname -o 2>/dev/null)" = "Msys" ] || [ "$(uname -o 2>/dev/null)" = "Cygwin" ]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" > /dev/null 2>&1
}

# Docker compose detection
get_compose_cmd() {
    if docker compose version > /dev/null 2>&1; then
        echo "docker compose"
    elif command_exists docker-compose; then
        echo "docker-compose"
    else
        echo ""
    fi
}

# Function to run compose commands
run_compose() {
    local compose_cmd=$(get_compose_cmd)
    if [ "$compose_cmd" = "docker compose" ]; then
        docker compose "$@"
    elif [ "$compose_cmd" = "docker-compose" ]; then
        docker-compose "$@"
    else
        print_error "Neither 'docker compose' nor 'docker-compose' is available"
        return 1
    fi
}

# Environment validation functions
check_python_env() {
    print_info "Checking Python environment..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        return 1
    fi
    
    # Check Python version
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_info "Found Python $python_version"
    
    # Don't check pip here - we'll check it in the virtual environment
    return 0
}

# Enhanced Python environment setup for API
setup_python_api_env() {
    print_info "Setting up Python environment for API..."
    
    # Detect Windows and handle Python properly
    local is_windows=false
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]] || command -v winpty >/dev/null 2>&1; then
        is_windows=true
    fi
    
    # Find Python executable - Windows-aware
    PYTHON_CMD=""
    if $is_windows; then
        # On Windows, check for various Python installations
        for py_candidate in "py" "python3" "python" "py.exe" "python3.exe" "python.exe"; do
            if command -v "$py_candidate" >/dev/null 2>&1; then
                # Test if it's actually Python and not MS Store redirect
                if "$py_candidate" --version >/dev/null 2>&1; then
                    PYTHON_CMD="$py_candidate"
                    break
                fi
            fi
        done
        
        # Special handling for Python Launcher on Windows
        if [ -z "$PYTHON_CMD" ] && command -v py >/dev/null 2>&1; then
            if py --version >/dev/null 2>&1; then
                PYTHON_CMD="py"
            fi
        fi
    else
        # On Linux/macOS
        if command_exists python3; then
            PYTHON_CMD="python3"
        elif command_exists python; then
            PYTHON_CMD="python"
        fi
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        print_error "No working Python installation found"
        if $is_windows; then
            print_info "Windows Python installation options:"
            print_info "1. Install from python.org: https://www.python.org/downloads/"
            print_info "2. Disable Microsoft Store Python alias:"
            print_info "   Settings > Apps > Advanced app settings > App execution aliases"
            print_info "   Turn OFF Python aliases"
            print_info "3. Install via Chocolatey: choco install python"
            print_info "4. Install via Scoop: scoop install python"
        else
            print_info "Install Python from: https://www.python.org/downloads/"
        fi
        return 1
    fi
    
    # Check Python version
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_info "Found Python $python_version using: $PYTHON_CMD"
    
    cd api || { print_error "api directory not found"; return 1; }
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_info "Activating existing virtual environment..."
        if [ -f "venv/Scripts/activate" ]; then
            # Windows
            source "venv/Scripts/activate"
        elif [ -f "venv/bin/activate" ]; then
            # Linux/macOS
            source "venv/bin/activate"
        else
            print_error "Virtual environment activation script not found"
            return 1
        fi
    else
        print_info "Creating new virtual environment..."
        
        # Create virtual environment with appropriate command
        if $is_windows && [ "$PYTHON_CMD" = "py" ]; then
            # Use Python Launcher on Windows
            if ! py -m venv venv; then
                print_error "Failed to create virtual environment with Python Launcher"
                # Try alternative
                if ! python -m venv venv 2>/dev/null; then
                    print_error "Failed to create virtual environment"
                    print_info "Try installing Python directly from python.org"
                    return 1
                fi
            fi
        else
            if ! $PYTHON_CMD -m venv venv; then
                print_error "Failed to create virtual environment"
                if $is_windows; then
                    print_info "Windows troubleshooting:"
                    print_info "1. Install Python from python.org (not Microsoft Store)"
                    print_info "2. Disable Microsoft Store Python aliases in Windows Settings"
                    print_info "3. Run: py -m pip install --user virtualenv"
                else
                    print_info "Try installing python3-venv: sudo apt install python3-venv"
                fi
                return 1
            fi
        fi
        
        print_info "Activating new virtual environment..."
        if [ -f "venv/Scripts/activate" ]; then
            # Windows
            source "venv/Scripts/activate"
        elif [ -f "venv/bin/activate" ]; then
            # Linux/macOS
            source "venv/bin/activate"
        else
            print_error "Virtual environment activation script not found"
            return 1
        fi
    fi
    
    # Verify virtual environment is active
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Virtual environment may not be fully activated, but continuing..."
    else
        print_success "Virtual environment activated: $VIRTUAL_ENV"
    fi
    
    # Upgrade pip in virtual environment
    print_info "Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_info "Installing dependencies from requirements.txt..."
        python -m pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            print_error "Failed to install dependencies"
            print_info "Check if requirements.txt has compatible package versions"
            return 1
        fi
    else
        print_error "requirements.txt not found"
        return 1
    fi
    
    return 0
}

check_node_env() {
    print_info "Checking Node.js environment..."
    
    if ! command_exists node; then
        print_error "Node.js is not installed or not in PATH"
        return 1
    fi
    
    node_version=$(node --version)
    print_info "Found Node.js $node_version"
    
    # Check package manager
    if command_exists yarn; then
        NPM_CMD="yarn"
    elif command_exists npm; then
        NPM_CMD="npm"
    else
        print_error "Neither npm nor yarn is available"
        return 1
    fi
    
    print_info "Using package manager: $NPM_CMD"
    return 0
}

check_mongodb() {
    print_info "Checking MongoDB..."
    
    if command_exists mongod; then
        print_success "MongoDB server found locally"
        return 0
    elif command_exists mongo || command_exists mongosh; then
        print_info "MongoDB client found (assuming remote connection)"
        return 0
    else
        print_warning "MongoDB not found locally - will need remote connection"
        return 1
    fi
}

check_docker() {
    print_info "Checking Docker environment..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    local compose_cmd=$(get_compose_cmd)
    if [ -z "$compose_cmd" ]; then
        print_error "Docker Compose is not available"
        return 1
    fi
    
    print_success "Docker and Docker Compose are ready"
    return 0
}

# Terminal execution functions
run_api_terminal() {
    print_info "Starting Flask API in terminal mode..."
    
    # Use the enhanced Python setup
    if ! setup_python_api_env; then
        print_error "Failed to setup Python environment"
        return 1
    fi
    
    # Set environment variables
    export FLASK_APP=app.main:app
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    print_success "Starting Flask API on http://localhost:5000"
    print_info "Press Ctrl+C to stop"
    
    # Run the Flask app
    python -m flask run --host=0.0.0.0 --port=5000 || flask run --host=0.0.0.0 --port=5000
}

run_frontend_terminal() {
    print_info "Starting React Frontend in terminal mode..."
    
    if ! check_node_env; then
        return 1
    fi
    
    cd frontend || { print_error "frontend directory not found"; return 1; }
    
    # Install dependencies
    print_info "Installing/updating dependencies..."
    if [ "$NPM_CMD" = "yarn" ]; then
        yarn install
    else
        npm install
    fi
    
    print_success "Starting React Frontend on http://localhost:3000"
    print_info "Press Ctrl+C to stop"
    
    # Run the development server
    if [ "$NPM_CMD" = "yarn" ]; then
        yarn start
    else
        npm start
    fi
}

run_mongodb_terminal() {
    print_info "Starting MongoDB in terminal mode..."
    
    if command_exists mongod; then
        print_info "Starting local MongoDB server..."
        # Create data directory if it doesn't exist
        mkdir -p data/db
        mongod --dbpath ./data/db --port 27017
    else
        print_warning "MongoDB server not found locally"
        print_info "Please ensure MongoDB is running remotely or install MongoDB locally"
        print_info "Connection string: mongodb://localhost:27017"
        return 1
    fi
}

run_legacy_terminal() {
    local app_name=$1
    print_info "Starting $app_name in terminal mode..."
    
    local app_dir="legacy/$app_name"
    if [ ! -d "$app_dir" ]; then
        print_error "$app_dir directory not found"
        return 1
    fi
    
    # Use python3 if available, otherwise python
    if command_exists python3; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    
    cd "$app_dir" || return 1
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment for $app_name..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        . venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        . venv/Scripts/activate
    fi
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        print_info "Installing dependencies for $app_name..."
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
    fi
    
    # Run the application
    if [ -f "app.py" ]; then
        print_success "Starting $app_name..."
        python app.py
    else
        print_error "app.py not found in $app_dir"
        return 1
    fi
}

# Docker execution functions (existing functionality)
run_docker_all() {
    print_info "Starting all services with Docker..."
    run_compose up -d
    
    print_success "Services running on:"
    echo "- New React Frontend: http://localhost:3000"
    echo "- New Flask API: http://localhost:5000/api/v1"
    echo "- Legacy Inventory: http://localhost:5001"
    echo "- Legacy Cash Register: http://localhost:5003"
    echo "- Legacy Calculator: http://localhost:5004"
    echo "- MongoDB: localhost:27017"
}

run_docker_new() {
    print_info "Starting new architecture with Docker..."
    run_compose up -d api frontend mongo
    
    print_success "New architecture running on:"
    echo "- React Frontend: http://localhost:3000"
    echo "- Flask API: http://localhost:5000/api/v1"
    echo "- MongoDB: localhost:27017"
}

run_docker_legacy() {
    print_info "Starting legacy applications with Docker..."
    run_compose up -d legacy-inventario legacy-caja legacy-calculadora
    
    print_success "Legacy applications running on:"
    echo "- Inventory: http://localhost:5001"
    echo "- Cash Register: http://localhost:5003"
    echo "- Calculator: http://localhost:5004"
}

# Main menu functions
show_execution_mode_menu() {
    clear
    echo "=== Inventario App Development Environment ==="
    echo "OS: $(detect_os)"
    echo ""
    echo "Choose execution mode:"
    echo "1. Docker mode (containerized)"
    echo "2. Terminal mode (native)"
    echo "3. Environment check"
    echo "4. Exit"
    echo ""
}

show_docker_menu() {
    echo ""
    echo "=== Docker Mode ==="
    echo "1. Start all services (legacy + new)"
    echo "2. Start only new architecture (API + Frontend + MongoDB)"
    echo "3. Start only legacy applications"
    echo "4. Stop all services"
    echo "5. View service status"
    echo "6. Reset and rebuild all containers"
    echo "7. View logs (all services)"
    echo "8. View logs (specific service)"
    echo "9. Back to main menu"
    echo ""
}

show_terminal_menu() {
    echo ""
    echo "=== Terminal Mode ==="
    echo "1. Start Flask API (run and exit)"
    echo "2. Start React Frontend (run and exit)"
    echo "3. Start MongoDB (run and exit)"
    echo "4. Start Legacy Inventory App (run and exit)"
    echo "5. Start Legacy Cash Register (run and exit)"
    echo "6. Start Legacy Calculator (run and exit)"
    echo "7. Start multiple services"
    echo "8. Check running services"
    echo "9. Stop background services"
    echo "10. Interactive mode (return to menu after service stops)"
    echo "11. Back to main menu"
    echo ""
}

show_terminal_menu_interactive() {
    echo "Interactive services (will return to menu when stopped):"
    echo "1. Flask API"
    echo "2. React Frontend" 
    echo "3. MongoDB"
    echo "4. Legacy Inventory App"
    echo "5. Legacy Cash Register"
    echo "6. Legacy Calculator"
    echo ""
}

handle_docker_menu() {
    show_docker_menu
    read -p "Choose an option (1-9): " docker_choice
    
    case $docker_choice in
        1) run_docker_all ;;
        2) run_docker_new ;;
        3) run_docker_legacy ;;
        4)
            print_info "Stopping all services..."
            run_compose down
            print_success "All services stopped."
            ;;
        5)
            print_info "Service status:"
            run_compose ps
            ;;
        6)
            print_info "Resetting and rebuilding all containers..."
            run_compose down -v
            run_compose build --no-cache
            run_compose up -d
            print_success "All containers rebuilt and started."
            ;;
        7)
            print_info "Viewing logs for all services..."
            run_compose logs -f
            ;;
        8)
            print_info "Available services:"
            run_compose ps --services
            echo ""
            read -p "Enter service name: " service
            print_info "Viewing logs for $service (Press Ctrl+C to exit)..."
            run_compose logs -f "$service"
            ;;
        9) return ;;
        *) print_error "Invalid option. Please choose 1-9." ;;
    esac
}

handle_terminal_menu() {
    show_terminal_menu
    read -p "Choose an option (1-11): " terminal_choice
    
    case $terminal_choice in
        1) 
            run_api_terminal
            print_info "API service has stopped. Exiting..."
            exit 0
            ;;
        2) 
            run_frontend_terminal
            print_info "Frontend service has stopped. Exiting..."
            exit 0
            ;;
        3) 
            run_mongodb_terminal
            print_info "MongoDB service has stopped. Exiting..."
            exit 0
            ;;
        4) 
            run_legacy_terminal "inventario_app"
            print_info "Legacy inventory service has stopped. Exiting..."
            exit 0
            ;;
        5) 
            run_legacy_terminal "caja"
            print_info "Legacy cash register service has stopped. Exiting..."
            exit 0
            ;;
        6) 
            run_legacy_terminal "calculadora_cambio"
            print_info "Legacy calculator service has stopped. Exiting..."
            exit 0
            ;;
        7)
            echo ""
            print_info "Multiple services mode options:"
            echo "1. Start API and Frontend sequentially (recommended)"
            echo "2. Generate startup commands (run in separate terminals)"
            echo "3. Start services in background (experimental)"
            echo ""
            read -p "Choose mode (1-3): " multi_mode
            
            case $multi_mode in
                1)
                    echo ""
                    print_info "Starting multiple services sequentially..."
                    echo "This will start the API first, then the Frontend."
                    echo "Press Ctrl+C to stop current service and move to next."
                    echo ""
                    read -p "Start API first? (y/n): " start_api
                    if [ "$start_api" = "y" ] || [ "$start_api" = "Y" ]; then
                        print_info "Starting API... (Press Ctrl+C when ready to start Frontend)"
                        run_api_terminal
                        echo ""
                        print_info "API stopped. Starting Frontend..."
                        run_frontend_terminal
                    else
                        print_info "Starting Frontend..."
                        run_frontend_terminal
                    fi
                    ;;
                2)
                    echo ""
                    print_info "Manual startup commands:"
                    echo ""
                    echo "Open separate terminals and run these commands:"
                    echo ""
                    echo "=== Terminal 1 (API) ==="
                    echo "cd $(pwd)/api"
                    if command_exists python3; then
                        echo "python3 -m venv venv"
                        echo "source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
                        echo "pip install -r requirements.txt"
                        echo "export FLASK_APP=app.main:app"
                        echo "export FLASK_ENV=development"
                        echo "export FLASK_DEBUG=1"
                        echo "flask run --host=0.0.0.0 --port=5000"
                    else
                        echo "python -m venv venv"
                        echo "source venv/bin/activate"
                        echo "pip install -r requirements.txt"
                        echo "set FLASK_APP=app.main:app"
                        echo "set FLASK_ENV=development"
                        echo "set FLASK_DEBUG=1"
                        echo "flask run --host=0.0.0.0 --port=5000"
                    fi
                    echo ""
                    echo "=== Terminal 2 (Frontend) ==="
                    echo "cd $(pwd)/frontend"
                    if command_exists yarn; then
                        echo "yarn install"
                        echo "yarn start"
                    else
                        echo "npm install"
                        echo "npm start"
                    fi
                    echo ""
                    echo "=== Terminal 3 (MongoDB) - Optional ==="
                    echo "mkdir -p data/db"
                    echo "mongod --dbpath ./data/db --port 27017"
                    echo ""
                    print_success "Copy and paste these commands in separate terminal windows."
                    ;;
                3)
                    echo ""
                    print_warning "Background mode is experimental and may not work properly."
                    read -p "Choose services (1=API, 2=Frontend, 3=MongoDB, combinations like 1,2): " services
                    
                    # Create log directory
                    mkdir -p logs
                    
                    if echo "$services" | grep -q "1"; then
                        print_info "Starting API in background..."
                        echo "Starting API..." > logs/api.log
                        (cd api && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && export FLASK_APP=app.main:app && export FLASK_ENV=development && export FLASK_DEBUG=1 && flask run --host=0.0.0.0 --port=5000) >> logs/api.log 2>&1 &
                        echo "API PID: $!" > logs/api.pid
                    fi
                    if echo "$services" | grep -q "2"; then
                        print_info "Starting Frontend in background..."
                        echo "Starting Frontend..." > logs/frontend.log
                        (cd frontend && npm install && npm start) >> logs/frontend.log 2>&1 &
                        echo "Frontend PID: $!" > logs/frontend.pid
                    fi
                    if echo "$services" | grep -q "3"; then
                        print_info "Starting MongoDB in background..."
                        echo "Starting MongoDB..." > logs/mongodb.log
                        (mkdir -p data/db && mongod --dbpath ./data/db --port 27017) >> logs/mongodb.log 2>&1 &
                        echo "MongoDB PID: $!" > logs/mongodb.pid
                    fi
                    
                    sleep 3
                    print_info "Background services started. Check logs in 'logs/' directory:"
                    ls -la logs/
                    echo ""
                    print_info "To monitor logs: tail -f logs/api.log"
                    print_info "To stop services: kill \$(cat logs/api.pid)"
                    ;;
            esac
            ;;
        8)
            print_info "Checking running services..."
            echo ""
            
            # Check for log files
            if [ -d "logs" ]; then
                echo "Background services status:"
                for service in api frontend mongodb; do
                    if [ -f "logs/${service}.pid" ]; then
                        pid=$(cat "logs/${service}.pid")
                        if ps -p $pid > /dev/null 2>&1; then
                            print_success "$service is running (PID: $pid)"
                        else
                            print_error "$service is not running (stale PID file)"
                        fi
                    else
                        print_info "$service: no background process"
                    fi
                done
            else
                print_info "No background services found"
            fi
            
            echo ""
            echo "Port usage:"
            netstat -tuln | grep -E ':(3000|5000|27017)' || print_info "No services found on standard ports"
            ;;
        9)
            print_info "Stopping background services..."
            
            if [ -d "logs" ]; then
                for service in api frontend mongodb; do
                    if [ -f "logs/${service}.pid" ]; then
                        pid=$(cat "logs/${service}.pid")
                        if ps -p $pid > /dev/null 2>&1; then
                            print_info "Stopping $service (PID: $pid)..."
                            kill $pid
                            sleep 2
                            if ps -p $pid > /dev/null 2>&1; then
                                print_warning "Force killing $service..."
                                kill -9 $pid
                            fi
                            rm -f "logs/${service}.pid"
                            print_success "$service stopped"
                        else
                            print_info "$service was not running"
                            rm -f "logs/${service}.pid"
                        fi
                    fi
                done
            else
                print_info "No background services to stop"
            fi
            ;;
        10)
            echo ""
            print_info "Interactive mode - services will return to menu when stopped"
            echo ""
            show_terminal_menu_interactive
            read -p "Choose a service to run interactively (1-6): " interactive_choice
            case $interactive_choice in
                1) run_api_terminal ;;
                2) run_frontend_terminal ;;
                3) run_mongodb_terminal ;;
                4) run_legacy_terminal "inventario_app" ;;
                5) run_legacy_terminal "caja" ;;
                6) run_legacy_terminal "calculadora_cambio" ;;
                *) print_error "Invalid option." ;;
            esac
            ;;
        11) return ;;
        *) print_error "Invalid option. Please choose 1-11." ;;
    esac
}

environment_check() {
    clear
    echo "=== Environment Check ==="
    echo ""
    
    print_info "Checking development environment..."
    echo ""
    
    # Check Docker
    if check_docker; then
        echo ""
    fi
    
    # Check Python
    if check_python_env; then
        echo ""
    fi
    
    # Check Node.js
    if check_node_env; then
        echo ""
    fi
    
    # Check MongoDB
    check_mongodb
    echo ""
    
    # Check project structure
    print_info "Checking project structure..."
    
    for dir in "api" "frontend" "legacy"; do
        if [ -d "$dir" ]; then
            print_success "$dir directory found"
        else
            print_warning "$dir directory not found"
        fi
    done
    
    echo ""
    print_info "Environment check completed!"
    echo ""
    read -p "Press Enter to continue..."
}

# Main program loop
main() {
    while true; do
        show_execution_mode_menu
        read -p "Choose an option (1-4): " mode_choice
        
        case $mode_choice in
            1)
                if check_docker; then
                    handle_docker_menu
                else
                    print_error "Docker is not available. Please install Docker or use Terminal mode."
                    echo ""
                    read -p "Press Enter to continue..."
                fi
                ;;
            2)
                handle_terminal_menu
                ;;
            3)
                environment_check
                ;;
            4)
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-4."
                sleep 2
                ;;
        esac
    done
}

# Run main program
main