---
name: dept-dashboard
description: French university department dashboard development with FastAPI backend, React frontend, CAS authentication, and department-scoped permissions. Use when working on features for data aggregation (ScoDoc, Parcoursup, Excel), budget tracking, recruitment analytics, scolarité indicators, or EDT management. Also use for authentication, permission systems, database migrations, adapter patterns, or adding new data sources.
---

# Dept-Dashboard Development Skill

French IUT department dashboard aggregating data from ScoDoc, Parcoursup, and Excel files with CAS authentication and granular department-scoped permissions.

## Quick Reference

**Tech Stack:** FastAPI + React + TypeScript + PostgreSQL + Redis + Alembic
**Python virtualenv:** `backend/venv/` (not `.venv`)
**Key patterns:** Adapter pattern, Permission dependencies, TanStack Query

## Common Tasks

### Adding a New Feature Endpoint

1. Add route in `backend/app/api/routes/{domain}.py` with permission dependency
2. Add Pydantic model in `backend/app/models/`
3. Add frontend API call in `frontend/src/services/api.ts`
4. Add permission check in frontend component using `useAuth()`

**Example:**

```python
# Backend
@router.get("/indicators")
async def get_indicators(user: UserDB = Depends(require_view_scolarite)):
    ...
```

```typescript
// Frontend
const { checkPermission } = useAuth()
const canView = checkPermission(department, 'can_view_budget')
```

### Adding a New Data Adapter

1. Create `backend/app/adapters/new_adapter.py` inheriting `BaseAdapter`
2. Implement `fetch_data()` and `health_check()` methods
3. Wire adapter in routes and cache scheduler

### Database Migrations

```bash
cd backend && alembic upgrade head  # Apply migrations
alembic revision --autogenerate -m "description"  # Create new
```

### Seeding Demo Data

```bash
python -m app.seeds --force  # CLI
curl -X POST "http://localhost:8000/api/admin/seed?force=true"  # API
```

## Architecture & Patterns

See [ARCHITECTURE.md](references/ARCHITECTURE.md) for:
- System architecture diagram
- Backend/frontend structure
- Database schema
- Adapter pattern implementation

## Permission System

See [PERMISSIONS.md](references/PERMISSIONS.md) for:
- Permission model (department-scoped)
- Backend route protection patterns
- Frontend permission gates
- Permission dependency factories

## Development Workflows

See [WORKFLOWS.md](references/WORKFLOWS.md) for:
- Adding new pages
- Adding new indicators
- Adding new data sources
- Testing procedures

## Python & TypeScript Conventions

See [CONVENTIONS.md](references/CONVENTIONS.md) for:
- Pydantic v2 patterns
- Async/await requirements
- React component patterns
- Naming conventions

## Critical Points

1. **Pydantic v2:** Use `model_dump()` not `.dict()`, `model_validate()` not `parse_obj()`
2. **All routes async:** Never block the event loop
3. **Virtualenv:** Located at `backend/venv/` (not `.venv`)
4. **Database agnostic:** Avoid SQLite-specific functions
5. **Permission checks:** Always check permissions before data access

## Running the Project

```bash
# Backend (from project root)
source backend/venv/bin/activate
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Docker
docker-compose up --build
```

## Files to Reference

- [backend/app/api/deps.py](../../backend/app/api/deps.py) - Permission system
- [frontend/src/contexts/AuthContext.tsx](../../frontend/src/contexts/AuthContext.tsx) - Auth state
- [AGENTS.md](../../AGENTS.md) - Comprehensive guide
- [DEPLOY.md](../../DEPLOY.md) - Production deployment
