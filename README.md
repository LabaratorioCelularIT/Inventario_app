# Inventario App - New Architecture

## Overview
This is the modernized version of the inventory management system using Flask REST API + React frontend with MongoDB database.

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
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local API development)

### Quick Start

1. **Start all services (legacy + new):**
   ```bash
   docker-compose up -d
   ```

2. **Access applications:**
   - New React Frontend: http://localhost:3000
   - New Flask API: http://localhost:5000
   - Legacy Inventory App: http://localhost:5001
   - Legacy Cash App: http://localhost:5003
   - Legacy Calculator App: http://localhost:5004
   - MongoDB: localhost:27017

3. **For local development:**
   ```bash
   # API development
   cd api
   pip install -r requirements.txt
   python app/main.py
   
   # Frontend development
   cd frontend
   npm install
   npm start
   ```

## Architecture Decision

**Chosen Stack:** Flask REST API + React Frontend + MongoDB

**Benefits:**
- ✅ Team keeps Flask knowledge
- ✅ Modern, scalable frontend
- ✅ Clean separation of concerns
- ✅ Easy to maintain and extend
- ✅ Gradual migration path

## Migration Strategy

### Phase 1: Infrastructure Setup (Week 1-2) ✅ COMPLETED
- [x] Repository restructuring
- [x] Docker development environment
- [x] Basic API and frontend scaffolding
- [x] Database setup (MongoDB + legacy SQLite)

### Phase 2: API Development (Week 3-8)
- [ ] Authentication system
- [ ] Inventory API endpoints
- [ ] Cash register API endpoints
- [ ] Data migration scripts
- [ ] API testing and documentation

### Phase 3: Frontend Development (Week 5-12)
- [ ] UI component library
- [ ] Authentication pages
- [ ] Inventory management interface
- [ ] Cash register interface
- [ ] Dashboard and reporting

### Phase 4: Integration & Testing (Week 13-16)
- [ ] End-to-end integration
- [ ] Performance optimization
- [ ] Security auditing
- [ ] User acceptance testing

### Phase 5: Production Deployment (Week 17-18)
- [ ] Production environment setup
- [ ] Data migration execution
- [ ] Gradual cutover
- [ ] Legacy system decommission

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

### Development Tools
- Docker & Docker Compose
- MongoDB for new data storage
- SQLite (legacy data, gradual migration)

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
3. Set up development environments
4. Begin Phase 2 API development
5. Start Phase 3 frontend development in parallel