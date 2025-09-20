# Inventario App - New Architecture

## Overview
This is the modernized version of the inventory management system using Flask REST API + React frontend with MongoDB database.

## 🚀 Quick Start

### Development Launcher (Recommended)
We provide enhanced development launchers for easy setup:

**Interactive Mode:**
```bash
./dev-launcher-enhanced.sh
```

**Direct Command Mode:**
```bash
# Start specific services directly
./dev-launcher-simple.sh api          # Flask API only
./dev-launcher-simple.sh frontend     # React frontend only  
./dev-launcher-simple.sh mongodb      # MongoDB only
```

**Features:**
- ✅ **Cross-platform support** (Windows, Linux, macOS)
- ✅ **Automatic environment detection** (Python, Node.js, Docker)
- ✅ **Virtual environment management**
- ✅ **Docker and native terminal modes**
- ✅ **Service monitoring and management**
- ✅ **Windows Python environment fixes**

See [`ENHANCED-LAUNCHER.md`](ENHANCED-LAUNCHER.md) for detailed documentation.

### Traditional Docker Setup
```bash
docker-compose up -d
```

## Project Structure

```
├── api/                    # Flask REST API (Backend)
│   ├── app/
│   │   ├── main.py        # Application factory
│   │   ├── config.py      # Configuration settings
│   │   ├── models/        # Database models (MongoDB/SQLAlchemy)
│   │   ├── api/v1/        # API endpoints
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service calls
│   │   ├── store/         # Redux store
│   │   └── styles/        # CSS styles
│   ├── package.json
│   └── Dockerfile
├── legacy/                # Current applications (business continuity)
│   ├── caja/             # Cash register app
│   ├── inventario_app/   # Inventory management app
│   ├── calculadora_cambio/ # Exchange calculator
│   ├── error-page/       # Error page components
│   └── inicio/           # Landing page components
└── shared/                # Shared resources
    ├── databases/        # Database files and migrations
    └── docker/           # Docker configurations
```

## Development Setup

### Prerequisites

- **For Docker mode:** Docker and Docker Compose
- **For terminal mode:** Python 3.11+, Node.js 18+, MongoDB (optional)

### Quick Start Options

**Option 1: Enhanced Development Launcher (Recommended)**

1. **Interactive launcher with menu:**
   ```bash
   ./dev-launcher-enhanced.sh
   ```

2. **Direct service launch:**
   ```bash
   # Launch specific services directly
   ./dev-launcher-simple.sh api          # Start Flask API
   ./dev-launcher-simple.sh frontend     # Start React frontend  
   ./dev-launcher-simple.sh mongodb      # Start MongoDB
   ```

**Option 2: Traditional Docker**

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access applications:**
   - New React Frontend: <http://localhost:3000>
   - New Flask API: <http://localhost:5000>  
   - Legacy Inventory App: <http://localhost:5001>
   - Legacy Cash App: <http://localhost:5003>
   - Legacy Calculator App: <http://localhost:5004>
   - MongoDB: localhost:27017

**Option 3: Manual Development Setup**

```bash
# API development (terminal mode)
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.main:app FLASK_ENV=development FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000

# Frontend development (separate terminal)  
cd frontend
npm install
npm start
```

### Development Tools

The enhanced launcher provides:

- **Environment detection** - Automatically finds Python/Node.js installations
- **Virtual environment management** - Creates and manages Python venvs
- **Cross-platform support** - Works on Windows, Linux, macOS
- **Service monitoring** - Track running processes and ports
- **Error handling** - Helpful error messages and troubleshooting
- **Multiple modes** - Docker containerized or native terminal execution

For detailed launcher documentation, see [`ENHANCED-LAUNCHER.md`](ENHANCED-LAUNCHER.md).

## Architecture Decision

**Chosen Stack:** Flask REST API + React Frontend + MongoDB

**Benefits:**
- ✅ Team keeps Flask knowledge
- ✅ Modern, scalable frontend
- ✅ Clean separation of concerns
- ✅ Easy to maintain and extend
- ✅ Gradual migration path

## Migration Strategy

### Phase 1: Infrastructure Setup ✅ COMPLETED

- [x] Repository restructuring  
- [x] Docker development environment
- [x] Flask API scaffolding with configuration management
- [x] React frontend scaffolding with TypeScript
- [x] MongoDB database setup
- [x] Cross-platform development launchers
- [x] Repository cleanup and security improvements
- [x] Virtual environment automation

### Phase 2: API Development (Week 3-8) 🚧 IN PROGRESS

- [ ] Authentication system (JWT)
- [ ] Inventory API endpoints (CRUD operations)
- [ ] Cash register API endpoints
- [ ] Data migration scripts (SQLite → MongoDB)
- [ ] API testing and documentation
- [x] Configuration management with dataclasses
- [x] Flask app factory pattern implementation

### Phase 3: Frontend Development (Week 5-12)

- [ ] UI component library setup
- [ ] Authentication pages (login/register)
- [ ] Inventory management interface
- [ ] Cash register interface  
- [ ] Dashboard and reporting components
- [ ] Redux store configuration
- [ ] API integration layer

### Phase 4: Integration & Testing (Week 13-16)

- [ ] End-to-end integration testing
- [ ] Performance optimization
- [ ] Security auditing  
- [ ] User acceptance testing
- [ ] Cross-browser compatibility
- [ ] Mobile responsiveness

### Phase 5: Production Deployment (Week 17-18)

- [ ] Production environment setup
- [ ] Data migration execution
- [ ] Gradual cutover strategy
- [ ] Legacy system decommission
- [ ] Documentation and training

## Port Allocation

- **3000**: New React Frontend
- **5000**: New Flask API
- **5001**: Legacy Inventory App
- **5003**: Legacy Cash App  
- **5004**: Legacy Calculator App
- **27017**: MongoDB

## Key Technologies

### Backend (API)

- Flask 2.3.3
- MongoDB with PyMongo  
- Flask-JWT-Extended for authentication
- Flask-CORS for cross-origin requests
- Marshmallow for serialization

### Frontend

- React 18
- TypeScript
- Redux Toolkit for state management
- React Router for navigation
- Axios for API calls

### Infrastructure & DevOps

- Docker & Docker Compose
- Enhanced development launchers (cross-platform)
- MongoDB for new data storage
- SQLite (legacy data, gradual migration)
- Automated virtual environment management

## Recent Improvements 🆕

### Development Experience
- ✅ **Cross-platform development launchers** with Windows support
- ✅ **Automated Python environment detection** and virtual environment setup  
- ✅ **Flask configuration management** with dataclasses and lazy loading
- ✅ **Repository security cleanup** - removed sensitive database files
- ✅ **Comprehensive .gitignore** - prevents tracking of build artifacts and dependencies

### Technical Fixes
- ✅ **Fixed Flask dataclass mutable defaults** - resolved startup errors
- ✅ **Implemented app factory pattern** - proper configuration management
- ✅ **Windows Python environment detection** - handles Microsoft Store Python redirects
- ✅ **Enhanced error handling** - better debugging information in launchers

## Team Distribution

See `WORK_DISTRIBUTION.md` for detailed task assignment and timeline.

## Legacy System Continuity

The legacy applications continue running unchanged during the migration:

- Business operations are not interrupted
- Data is preserved and accessible  
- Easy rollback if needed
- Gradual feature migration

## Next Steps

1. Review and approve the architecture setup
2. Assign team members to specific phases  
3. Set up development environments using enhanced launchers
4. Begin Phase 2 API development (authentication system)
5. Start Phase 3 frontend development in parallel