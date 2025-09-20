#!/usr/bin/env bash

# Setup script for Inventario App Development Environment
# Handles cross-platform setup and dependencies

echo "=== Inventario App Setup ==="

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

OS=$(detect_os)
echo "Detected OS: $OS"

# Install dos2unix if needed
install_dos2unix() {
    if command -v dos2unix &> /dev/null; then
        echo "✓ dos2unix is already installed"
        return
    fi

    echo "Installing dos2unix..."
    case $OS in
        "linux")
            if command -v apt &> /dev/null; then
                sudo apt update && sudo apt install -y dos2unix
            elif command -v yum &> /dev/null; then
                sudo yum install -y dos2unix
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y dos2unix
            else
                echo "Please install dos2unix manually for your Linux distribution"
                exit 1
            fi
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install dos2unix
            else
                echo "Please install Homebrew first: https://brew.sh/"
                echo "Then run: brew install dos2unix"
                exit 1
            fi
            ;;
        "windows")
            echo "For Windows, please install dos2unix using:"
            echo "- Chocolatey: choco install dos2unix"
            echo "- Scoop: scoop install dos2unix"
            echo "Or use the cross-platform script which handles line endings automatically"
            ;;
        *)
            echo "Unsupported OS for automatic installation"
            ;;
    esac
}

# Fix script permissions and line endings
fix_scripts() {
    echo "Fixing script permissions and line endings..."
    
    # List of scripts to fix
    scripts=("dev-launcher.sh" "dev-launcher-cross-platform.sh")
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            echo "Processing $script..."
            
            # Fix line endings if dos2unix is available
            if command -v dos2unix &> /dev/null; then
                dos2unix "$script"
            fi
            
            # Make executable
            chmod +x "$script"
            echo "✓ $script is now executable"
        fi
    done
}

# Check Docker installation
check_docker() {
    echo "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        echo "✓ Docker is installed"
        docker --version
    else
        echo "❌ Docker is not installed"
        echo "Please install Docker:"
        case $OS in
            "linux")
                echo "- Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
                ;;
            "macos")
                echo "- Download Docker Desktop: https://docs.docker.com/desktop/mac/"
                ;;
            "windows")
                echo "- Download Docker Desktop: https://docs.docker.com/desktop/windows/"
                ;;
        esac
        return 1
    fi
    
    # Check Docker Compose
    if docker compose version &> /dev/null; then
        echo "✓ Docker Compose (built-in) is available"
        docker compose version
    elif command -v docker-compose &> /dev/null; then
        echo "✓ Docker Compose (standalone) is available"
        docker-compose --version
    else
        echo "❌ Docker Compose is not available"
        echo "Please install Docker Compose or update Docker to a newer version"
        return 1
    fi
}

# Main setup process
main() {
    echo ""
    echo "Starting setup process..."
    echo ""
    
    # Install dos2unix
    install_dos2unix
    
    # Fix scripts
    fix_scripts
    
    # Check Docker
    if check_docker; then
        echo ""
        echo "✓ Setup completed successfully!"
        echo ""
        echo "You can now run the development launcher:"
        echo "  ./dev-launcher-cross-platform.sh  (recommended for cross-platform)"
        echo "  ./dev-launcher.sh                 (original version)"
    else
        echo ""
        echo "❌ Setup incomplete - Docker issues detected"
        echo "Please install Docker and Docker Compose, then run this setup again"
        exit 1
    fi
}

main