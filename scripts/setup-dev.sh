#!/bin/bash

# Development Environment Setup Script
# Run this to set up both legacy and new development environments

set -e

echo "🚀 Setting up development environment..."

# Create new directory structure
echo "📁 Creating directory structure..."
mkdir -p api/app/{models,api/v1,services,utils,migrations}
mkdir -p api/tests
mkdir -p frontend/src/{components/{common,inventory,sales},pages,hooks,services,store,types,utils,styles}
mkdir -p shared/{databases,docker}
mkdir -p scripts
mkdir -p docs

# Setup API environment
echo "🐍 Setting up Flask API environment..."
cd api
python -m venv venv
source venv/bin/activate
pip install flask flask-pymongo flask-cors flask-jwt-extended marshmallow python-dotenv pytest

# Create requirements.txt
cat > requirements.txt << EOF
Flask==2.3.3
Flask-PyMongo==2.3.0
Flask-CORS==4.0.0
Flask-JWT-Extended==4.5.3
marshmallow==3.20.1
python-dotenv==1.0.0
pytest==7.4.2
pymongo==4.5.0
bcrypt==4.0.1
celery==5.3.2
redis==4.6.0
EOF

cd ..

# Setup Frontend environment
echo "⚛️ Setting up React frontend..."
cd frontend
npm init -y
npm install react react-dom @types/react @types/react-dom typescript
npm install -D vite @vitejs/plugin-react tailwindcss postcss autoprefixer
npm install axios @tanstack/react-query zustand react-hook-form @hookform/resolvers zod
npm install lucide-react date-fns

# Create package.json scripts
cat > package.json << EOF
{
  "name": "inventario-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.5.0",
    "@tanstack/react-query": "^4.33.0",
    "zustand": "^4.4.1",
    "react-hook-form": "^7.46.1",
    "@hookform/resolvers": "^3.3.1",
    "zod": "^3.22.2",
    "lucide-react": "^0.276.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5",
    "tailwindcss": "^3.3.3",
    "postcss": "^8.4.29",
    "autoprefixer": "^10.4.15"
  }
}
EOF

cd ..

# Create Docker configurations
echo "🐳 Creating Docker configurations..."
cat > docker-compose.dev.yml << EOF
version: '3.9'

services:
  # Legacy services (keep running)
  legacy-inventario:
    build: ./legacy/inventario_app
    container_name: legacy_inventario
    ports:
      - "5001:5001"
    volumes:
      - ./shared/databases/inventario.sqlite3:/app/inventario.sqlite3
    environment:
      - FLASK_ENV=development
      - INVENTARIO_DB=/app/inventario.sqlite3

  legacy-caja:
    build: ./legacy/caja
    container_name: legacy_caja
    ports:
      - "5003:5003"
    volumes:
      - ./shared/databases/inventario.sqlite3:/app/inventario.sqlite3
    environment:
      - FLASK_ENV=development
      - INVENTARIO_DB=/app/inventario.sqlite3

  # New services (development)
  api:
    build: ./api
    container_name: new_api
    ports:
      - "5000:5000"
    volumes:
      - ./api:/app
      - ./shared/databases:/shared/databases
    environment:
      - FLASK_ENV=development
      - MONGO_URI=mongodb://mongodb:27017/inventario_new
      - LEGACY_DB_PATH=/shared/databases/inventario.sqlite3
    depends_on:
      - mongodb
      - redis

  frontend-dev:
    build: ./frontend
    container_name: new_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_BASE_URL=http://localhost:5000/api/v1

  mongodb:
    image: mongo:6.0
    container_name: mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./shared/databases/mongo-init:/docker-entrypoint-initdb.d
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password123
      - MONGO_INITDB_DATABASE=inventario_new

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"

volumes:
  mongodb_data:
EOF

# Move current apps to legacy
echo "📦 Moving current apps to legacy directory..."
mkdir -p legacy
if [ -d "caja" ] && [ ! -d "legacy/caja" ]; then
    cp -r caja legacy/
fi
if [ -d "inventario_app" ] && [ ! -d "legacy/inventario_app" ]; then
    cp -r inventario_app legacy/
fi
if [ -d "calculadora_cambio" ] && [ ! -d "legacy/calculadora_cambio" ]; then
    cp -r calculadora_cambio legacy/
fi

# Move shared database
echo "🗄️ Setting up shared database..."
mkdir -p shared/databases
if [ -f "inventario.sqlite3" ]; then
    cp inventario.sqlite3 shared/databases/
fi

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Run 'docker-compose -f docker-compose.dev.yml up -d' to start all services"
echo "2. Access legacy inventory at: http://localhost:5001"
echo "3. Access legacy caja at: http://localhost:5003"  
echo "4. New API will be at: http://localhost:5000"
echo "5. New frontend will be at: http://localhost:3000"
echo ""
echo "Legacy apps will continue running while you develop the new ones!"