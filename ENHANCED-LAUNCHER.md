# Enhanced Development Launcher - Setup Guide

## Features

### Execution Modes
- **Docker Mode**: Run services in containers (original functionality)
- **Terminal Mode**: Run services natively on your system
- **Environment Check**: Validate your development environment

### Terminal Mode Benefits
- 🚀 **Faster startup** - No container overhead
- 🔧 **Easy debugging** - Direct access to logs and code
- 💾 **Lower resource usage** - No Docker daemon required
- 🔄 **Hot reloading** - Changes reflect immediately
- 🌍 **Cross-platform** - Works on Windows, macOS, Linux

## Quick Start

### 1. Make the script executable
```bash
chmod +x dev-launcher-enhanced.sh
```

### 2. Run the enhanced launcher
```bash
./dev-launcher-enhanced.sh
```

### 3. Choose your execution mode
- **Option 1**: Docker mode (if Docker is available)
- **Option 2**: Terminal mode (native execution)
- **Option 3**: Environment check (validate dependencies)

## Terminal Mode Requirements

### For API (Flask)
- Python 3.8+ (`python3` or `python`)
- pip (`python -m pip`)
- Virtual environment support

### For Frontend (React)
- Node.js 16+ (`node`)
- npm or yarn (`npm` or `yarn`)

### For MongoDB
- Local: MongoDB server (`mongod`)
- Remote: MongoDB client (`mongo` or `mongosh`)

### For Legacy Apps
- Python 3.8+ with Flask

## Terminal Mode Usage

### Individual Services
1. Choose **Terminal Mode**
2. Select individual service:
   - Flask API (runs on http://localhost:5000)
   - React Frontend (runs on http://localhost:3000)
   - MongoDB (runs on localhost:27017)
   - Legacy applications (various ports)

### Multiple Services
1. Choose **Terminal Mode** → **Option 7**
2. Select services to run in background
3. Services run simultaneously in separate processes

### Development Workflow
```bash
# Environment check first
./dev-launcher-enhanced.sh
# Choose: 3 (Environment check)

# Start API for backend development
./dev-launcher-enhanced.sh
# Choose: 2 (Terminal mode) → 1 (Start Flask API)

# In another terminal, start Frontend
./dev-launcher-enhanced.sh
# Choose: 2 (Terminal mode) → 2 (Start React Frontend)
```

## What Terminal Mode Does

### Flask API Terminal Mode
1. Creates/activates virtual environment (`venv/`)
2. Installs dependencies from `requirements.txt`
3. Sets Flask environment variables
4. Starts development server with hot reload

### React Frontend Terminal Mode
1. Detects npm/yarn package manager
2. Installs/updates dependencies
3. Starts development server with hot reload
4. Opens in default browser (if available)

### MongoDB Terminal Mode
1. Creates data directory (`data/db/`)
2. Starts local MongoDB server
3. Provides connection information

## Troubleshooting

### Python Issues
```bash
# Check Python installation
python3 --version
python --version

# Check pip
python3 -m pip --version

# Install missing packages
pip install -r api/requirements.txt
```

### Node.js Issues
```bash
# Check Node.js
node --version

# Check package managers
npm --version
yarn --version

# Install dependencies
cd frontend && npm install
```

### MongoDB Issues
```bash
# Check MongoDB
mongod --version

# Install MongoDB (Ubuntu/Debian)
sudo apt update
sudo apt install mongodb

# Install MongoDB (macOS)
brew install mongodb-community

# Install MongoDB (Windows)
# Download from: https://www.mongodb.com/try/download/community
```

### Permission Issues
```bash
# Fix script permissions
chmod +x dev-launcher-enhanced.sh

# Fix Python virtual environment
rm -rf api/venv
cd api && python3 -m venv venv
```

## Environment Variables

### Terminal Mode Environment Variables
The script automatically sets these for Flask API:
- `FLASK_APP=app.main:app`
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`

### Custom Configuration
Create a `.env` file in the project root:
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/inventario

# API
API_PORT=5000
API_HOST=localhost

# Frontend
REACT_APP_API_URL=http://localhost:5000/api/v1
```

## Comparison: Docker vs Terminal Mode

| Feature | Docker Mode | Terminal Mode |
|---------|-------------|---------------|
| Setup | Requires Docker | Requires dev tools |
| Startup Time | Slower | Faster |
| Resource Usage | Higher | Lower |
| Isolation | Complete | Shared system |
| Debugging | Container logs | Direct access |
| Hot Reload | Limited | Full support |
| Production-like | Yes | No |
| Cross-platform | Yes | Depends on tools |

## Best Practices

### Development
- Use **Terminal Mode** for active development
- Use **Docker Mode** for integration testing
- Run **Environment Check** first on new systems

### Team Collaboration
- Provide both modes for different preferences
- Document system requirements clearly
- Include environment setup in README

### Deployment
- Always test with **Docker Mode** before deployment
- Use Docker for production deployments
- Keep both modes in sync with dependencies