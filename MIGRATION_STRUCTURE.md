# Migration Repository Structure Plan

## Proposed Directory Structure

```
Inventario_app/
├── legacy/                          # Current applications (keep running)
│   ├── caja/                       # Current cash register app
│   │   ├── app.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── requirements.txt
│   ├── inventario_app/             # Current inventory app
│   │   ├── app.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── requirements.txt
│   └── calculadora_cambio/         # Current calculator app
│       └── ...
├── api/                            # New Flask API backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/                 # MongoDB models
│   │   │   ├── __init__.py
│   │   │   ├── inventory.py
│   │   │   ├── sales.py
│   │   │   ├── users.py
│   │   │   └── base.py
│   │   ├── api/                    # API blueprints
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── inventory.py
│   │   │       ├── sales.py
│   │   │       ├── reports.py
│   │   │       └── users.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── inventory_service.py
│   │   │   ├── sales_service.py
│   │   │   ├── auth_service.py
│   │   │   └── report_service.py
│   │   ├── utils/                  # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── validators.py
│   │   │   ├── helpers.py
│   │   │   ├── decorators.py
│   │   │   └── exceptions.py
│   │   ├── migrations/             # Data migration scripts
│   │   │   ├── __init__.py
│   │   │   ├── sqlite_to_mongo.py
│   │   │   └── data_transform.py
│   │   └── config.py
│   ├── tests/                      # API tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_inventory.py
│   │   └── test_sales.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/                       # New React frontend
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/             # Reusable components
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── inventory/
│   │   │   │   ├── InventoryList.tsx
│   │   │   │   ├── InventoryForm.tsx
│   │   │   │   └── TransferForm.tsx
│   │   │   └── sales/
│   │   │       ├── SalesList.tsx
│   │   │       ├── POSInterface.tsx
│   │   │       └── ReportsView.tsx
│   │   ├── pages/                  # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Inventory.tsx
│   │   │   ├── Sales.tsx
│   │   │   ├── Reports.tsx
│   │   │   └── Login.tsx
│   │   ├── hooks/                  # Custom hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useInventory.ts
│   │   │   └── useSales.ts
│   │   ├── services/               # API calls
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── inventory.ts
│   │   │   └── sales.ts
│   │   ├── store/                  # State management
│   │   │   ├── authStore.ts
│   │   │   ├── inventoryStore.ts
│   │   │   └── salesStore.ts
│   │   ├── types/                  # TypeScript definitions
│   │   │   ├── auth.ts
│   │   │   ├── inventory.ts
│   │   │   └── sales.ts
│   │   ├── utils/
│   │   │   ├── constants.ts
│   │   │   ├── helpers.ts
│   │   │   └── validators.ts
│   │   ├── styles/                 # Global styles
│   │   │   └── globals.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── shared/                         # Shared resources
│   ├── databases/
│   │   ├── inventario.sqlite3      # Current shared DB
│   │   └── mongo-init/             # MongoDB initialization scripts
│   │       └── init.js
│   └── docker/
│       └── nginx.conf              # Reverse proxy config
├── scripts/                        # Utility scripts
│   ├── setup-dev.sh               # Development environment setup
│   ├── migrate-data.py             # Data migration script
│   └── deploy.sh                   # Deployment script
├── docs/                           # Documentation
│   ├── API.md                     # API documentation
│   ├── MIGRATION.md               # Migration guide
│   └── DEPLOYMENT.md              # Deployment guide
├── docker-compose.yml             # Updated for new architecture
├── docker-compose.legacy.yml      # Keep legacy running
├── .gitignore
└── README.md
```

## Migration Phases

### Phase 1: Setup New Structure (Week 1-2)
1. Create new directories without touching legacy
2. Setup development environments
3. Initialize new Docker configurations

### Phase 2: Parallel Development (Week 3-10)
1. Develop API in `api/` directory
2. Develop React app in `frontend/` directory  
3. Keep legacy apps running for business continuity

### Phase 3: Integration & Testing (Week 11-14)
1. Connect frontend to API
2. Data migration from SQLite to MongoDB
3. End-to-end testing

### Phase 4: Gradual Cutover (Week 15-16)
1. Deploy new system alongside legacy
2. Route specific features to new system
3. Monitor and fix issues
4. Complete migration

### Phase 5: Cleanup (Week 17-18)
1. Remove legacy code
2. Update documentation
3. Final optimizations

## Docker Configuration Strategy

### Development (Both Systems)
```yaml
# docker-compose.dev.yml
version: '3.9'
services:
  # Legacy services (keep running)
  legacy-inventario:
    build: ./legacy/inventario_app
    ports: ["5001:5001"]
    
  legacy-caja:
    build: ./legacy/caja  
    ports: ["5003:5003"]
    
  # New services (development)
  api:
    build: ./api
    ports: ["5000:5000"]
    depends_on: [mongodb]
    
  frontend-dev:
    build: ./frontend
    ports: ["3000:3000"]
    volumes: ["./frontend:/app"]
    
  mongodb:
    image: mongo:6.0
    ports: ["27017:27017"]
```

### Production (Gradual Migration)
```yaml
# docker-compose.prod.yml  
version: '3.9'
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./shared/docker/nginx.conf:/etc/nginx/nginx.conf"]
    depends_on: [api, frontend]
    
  api:
    build: ./api
    environment:
      - MONGO_URI=mongodb://mongodb:27017/inventario
      
  frontend:
    build: ./frontend
    
  mongodb:
    image: mongo:6.0
    volumes: ["mongodb_data:/data/db"]
```

## URL Routing Strategy

### Nginx Configuration for Gradual Migration
```nginx
# /shared/docker/nginx.conf
upstream legacy_inventario {
    server legacy-inventario:5001;
}

upstream legacy_caja {
    server legacy-caja:5003;
}

upstream new_api {
    server api:5000;
}

upstream new_frontend {
    server frontend:3000;
}

server {
    listen 80;
    
    # New API routes
    location /api/ {
        proxy_pass http://new_api;
    }
    
    # New frontend (gradually migrate paths)
    location /app/ {
        proxy_pass http://new_frontend;
        rewrite ^/app(.*)$ $1 break;
    }
    
    # Legacy routes (keep during migration)
    location /legacy/inventario/ {
        proxy_pass http://legacy_inventario;
        rewrite ^/legacy/inventario(.*)$ $1 break;
    }
    
    location /legacy/caja/ {
        proxy_pass http://legacy_caja;
        rewrite ^/legacy/caja(.*)$ $1 break;
    }
    
    # Default to legacy for now
    location / {
        proxy_pass http://legacy_inventario;
    }
}
```