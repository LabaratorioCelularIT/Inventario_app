# Migration Strategy Documentation

## Repository Structure During Migration

This document outlines the strategy for maintaining both legacy and new systems during the migration process.

## Key Benefits of This Approach

### ✅ Zero Downtime Migration
- Legacy systems continue running unchanged
- New system developed in parallel
- Gradual feature-by-feature migration
- Business operations never interrupted

### ✅ Risk Mitigation
- Easy rollback if issues arise
- Side-by-side comparison during development
- Independent testing environments
- Incremental validation

### ✅ Team Productivity
- Different team members can work on different parts
- No blocking dependencies between legacy and new development
- Clear separation of concerns

## Migration Phases

### Phase 1: Environment Setup (Weeks 1-2)
**Goal**: Establish parallel development environment

**Actions**:
1. Run `scripts/setup-dev.sh` to create new structure
2. Move existing apps to `legacy/` directory
3. Setup Docker environments for both systems
4. Verify both legacy and new environments work

**Success Criteria**:
- Legacy apps accessible at localhost:5001, localhost:5003
- New development environment ready
- MongoDB and Redis containers running
- No disruption to current operations

### Phase 2: API Development (Weeks 3-8)
**Goal**: Build complete REST API backend

**Focus Areas**:
```
api/app/
├── models/          # MongoDB data models
├── api/v1/         # REST endpoints
├── services/       # Business logic layer
└── utils/          # Helper functions
```

**Key Endpoints to Implement**:
- Authentication (`/api/v1/auth`)
- Inventory management (`/api/v1/inventory`)
- Sales operations (`/api/v1/sales`)
- Reports (`/api/v1/reports`)
- User management (`/api/v1/users`)

### Phase 3: Frontend Development (Weeks 6-10)
**Goal**: Build modern React frontend

**Focus Areas**:
```
frontend/src/
├── components/     # Reusable UI components
├── pages/          # Application pages  
├── services/       # API communication
└── store/          # State management
```

**Key Features**:
- Modern dashboard with real-time updates
- Inventory management interface
- Point of sale system
- Reporting and analytics
- User management

### Phase 4: Integration (Weeks 11-14)
**Goal**: Connect frontend to API and migrate data

**Actions**:
1. Frontend-API integration
2. Data migration from SQLite to MongoDB
3. End-to-end testing
4. Performance optimization

### Phase 5: Gradual Cutover (Weeks 15-16)
**Goal**: Migrate users to new system

**Strategy**:
1. Deploy new system with different URL paths
2. Migrate specific features/users gradually
3. Use nginx routing to direct traffic
4. Monitor and fix issues in real-time

### Phase 6: Cleanup (Weeks 17-18)
**Goal**: Remove legacy code and optimize

**Actions**:
1. Remove legacy directories
2. Update documentation
3. Optimize performance
4. Final testing

## URL Routing During Migration

### Development Phase
```
http://localhost:5001  → Legacy Inventory
http://localhost:5003  → Legacy Caja  
http://localhost:5000  → New API
http://localhost:3000  → New Frontend
```

### Production Migration Phase
```nginx
# Nginx configuration for gradual migration
location /api/          → New API
location /app/          → New Frontend
location /legacy/inv/   → Legacy Inventory  
location /legacy/caja/  → Legacy Caja
location /             → Legacy (default)
```

### Post-Migration
```nginx  
location /api/  → New API
location /      → New Frontend
```

## Docker Configuration Strategy

### Development (Both Systems Running)
```yaml
# docker-compose.dev.yml
services:
  # Legacy services
  legacy-inventario:   # Port 5001
  legacy-caja:         # Port 5003
  
  # New services  
  api:                 # Port 5000
  frontend-dev:        # Port 3000
  mongodb:             # Port 27017
  redis:               # Port 6379
```

### Production Migration
```yaml
# docker-compose.prod.yml
services:
  nginx:               # Routes traffic
  api:                 # New backend
  frontend:            # New frontend
  mongodb:             # New database
  
  # Keep legacy during transition
  legacy-inventario:   # Backup system
  legacy-caja:         # Backup system
```

## Data Migration Strategy

### Dual-Database Approach
- Keep SQLite for legacy systems
- MongoDB for new system
- Migration script transfers data
- Validation ensures data integrity

### Migration Script Usage
```bash
# Run data migration
python scripts/migrate-data.py /shared/databases/inventario.sqlite3 mongodb://localhost:27017/inventario_new

# Validate migration
python scripts/validate-migration.py
```

## Testing Strategy

### Parallel Testing
- Legacy system: Continue current testing
- New system: Comprehensive test suite
- Integration tests: API + Frontend
- Performance tests: Load and stress testing

### Data Validation
- Compare legacy vs new system outputs
- Verify business logic consistency
- Test edge cases and error handling

## Rollback Strategy

### If Issues Arise
1. **Stop new system containers**
2. **Update nginx to route all traffic to legacy**
3. **Investigate and fix issues**
4. **Re-deploy when ready**

### Quick Rollback Commands
```bash
# Emergency rollback
docker-compose -f docker-compose.prod.yml stop api frontend
nginx -s reload  # With legacy-only configuration

# Resume migration
docker-compose -f docker-compose.prod.yml up -d api frontend
nginx -s reload  # With migration configuration
```

## Success Metrics

### Technical Metrics
- API response times < 200ms
- Frontend load times < 2s
- Database query performance
- Zero data loss during migration

### Business Metrics
- No interruption to daily operations
- User adoption rate of new features
- Error rates and support tickets
- Overall system reliability

## Next Steps

1. **Review this strategy** with your team
2. **Run setup script** to establish development environment  
3. **Begin API development** while legacy continues operating
4. **Plan detailed timeline** with specific milestones
5. **Assign team responsibilities** for different components

This approach ensures a smooth, low-risk migration while maintaining business continuity throughout the process.