#!/bin/bash

# Simple Windows Development Launcher
# Direct service launchers without menus - perfect for Windows terminals

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

# Check if command exists
command_exists() {
    command -v "$1" > /dev/null 2>&1
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
                return 1
            fi
        else
            if ! $PYTHON_CMD -m venv venv; then
                print_error "Failed to create virtual environment"
                if $is_windows; then
                    print_info "Windows troubleshooting:"
                    print_info "1. Install Python from python.org (not Microsoft Store)"
                    print_info "2. Disable Microsoft Store Python aliases in Windows Settings"
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
            return 1
        fi
    else
        print_error "requirements.txt not found"
        return 1
    fi
    
    return 0
}

# Direct service functions
start_api() {
    echo "=== Starting Flask API ==="
    
    if ! setup_python_api_env; then
        print_error "Failed to setup Python environment"
        exit 1
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

start_frontend() {
    echo "=== Starting React Frontend ==="
    
    if ! command_exists node; then
        print_error "Node.js is not installed or not in PATH"
        print_info "Install Node.js from: https://nodejs.org/"
        exit 1
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
        exit 1
    fi
    
    print_info "Using package manager: $NPM_CMD"
    
    cd frontend || { print_error "frontend directory not found"; exit 1; }
    
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

start_mongodb() {
    echo "=== Starting MongoDB ==="
    
    if command_exists mongod; then
        print_info "Starting local MongoDB server..."
        # Create data directory if it doesn't exist
        mkdir -p data/db
        print_success "MongoDB will run on localhost:27017"
        print_info "Press Ctrl+C to stop"
        mongod --dbpath ./data/db --port 27017
    else
        print_error "MongoDB server not found locally"
        print_info "Install MongoDB from: https://www.mongodb.com/try/download/community"
        exit 1
    fi
}

# Check command line argument
case "$1" in
    "api"|"API")
        start_api
        ;;
    "frontend"|"FRONTEND"|"react"|"REACT")
        start_frontend
        ;;
    "mongodb"|"MONGODB"|"mongo"|"MONGO"|"db"|"DB")
        start_mongodb
        ;;
    *)
        echo "=== Simple Windows Development Launcher ==="
        echo ""
        echo "Usage: $0 [service]"
        echo ""
        echo "Available services:"
        echo "  api       - Start Flask API server"
        echo "  frontend  - Start React development server"
        echo "  mongodb   - Start MongoDB server"
        echo ""
        echo "Examples:"
        echo "  $0 api       # Start Flask API"
        echo "  $0 frontend  # Start React frontend"
        echo "  $0 mongodb   # Start MongoDB"
        echo ""
        echo "Each service will run until you press Ctrl+C"
        echo "Perfect for Windows development in separate terminals!"
        ;;
esac