# Copilot Instructions - Dept-Dashboard

## Project Overview
University department dashboard (French IUT) aggregating data from ScoDoc, Parcoursup, Excel files. Multi-department support with CAS authentication and granular permissions.

## Architecture

```
Frontend (React/Vite/TS) → FastAPI Backend → Adapters → Data Sources
                              ↓
                    SQLite/PostgreSQL (users) + Redis (cache)
```

**Key boundaries:**
- `backend/app/adapters/` - Data source connectors (inherit from `BaseAdapter`)
- `backend/app/api/routes/` - Domain routes + `*_admin.py` for CRUD operations
- `backend/app/api/deps.py` - Auth dependencies, permission checkers
- `frontend/src/contexts/AuthContext.tsx` - Client-side auth state

## Authentication & Permissions

**Permission model:** Department-scoped (`RT`, `GEII`, `GCCD`, `GMP`, `QLIO`, `CHIMIE`)

```python
# Backend route protection pattern
from app.api.deps import require_view_budget, require_edit_budget

@router.get("/indicators")
async def get_indicators(user: UserDB = Depends(require_view_budget)):
    ...

@router.post("/")  
async def create(user: UserDB = Depends(require_edit_budget)):
    ...
```

```typescript
// Frontend permission filtering
const { checkPermission } = useAuth()
const canView = checkPermission(department, 'can_view_budget')
```

**Dev auth:** Set `CAS_USE_MOCK=true` in `.env`, use dev login form with any username.

## Critical Conventions

### Backend (Python)
- **Pydantic v2**: Use `model_dump()` not `.dict()`, `model_validate()` not `parse_obj()`
- **All routes async**: Never block event loop
- **Virtualenv location**: `backend/venv/` (not `.venv`)
- **Run backend**: `cd backend && uvicorn app.main:app --reload`

### Frontend (TypeScript)
- **Data fetching**: Always use TanStack Query with `queryKey` arrays
- **API client**: All calls via `frontend/src/services/api.ts` with axios interceptor for auth
- **Auth token**: Stored in `localStorage` as `auth_token`

### Database
- **Dev**: SQLite at `backend/data/dashboard.db`
- **Prod**: PostgreSQL via `DATABASE_URL` env var
- **Migrations**: Alembic in `backend/alembic/`

## Adding Features

### New API endpoint
1. Add route in `backend/app/api/routes/{domain}.py`
2. Add permission dependency from `deps.py` if protected
3. Add Pydantic model in `backend/app/models/`
4. Add frontend API call in `frontend/src/services/api.ts`

### New data adapter
1. Create `backend/app/adapters/new_adapter.py` inheriting `BaseAdapter`
2. Implement `fetch_data()` and `health_check()`
3. Wire in routes and cache scheduler

### New page with permission check
1. Create page in `frontend/src/pages/`
2. Add route in `App.tsx` inside `<ProtectedRoute>`
3. Add nav item in `Layout.tsx` with permission filter
4. Handle 403 errors in the page component

## Commands

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
pytest -v

# Frontend  
cd frontend && npm run dev

# Migrations
cd backend && alembic upgrade head
alembic revision --autogenerate -m "description"

# Production
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Files to Reference
- [AGENTS.md](../AGENTS.md) - Detailed patterns and conventions
- [DEPLOY.md](../DEPLOY.md) - Production deployment guide
- [backend/app/api/deps.py](../backend/app/api/deps.py) - Permission system implementation
- [frontend/src/contexts/AuthContext.tsx](../frontend/src/contexts/AuthContext.tsx) - Auth state management
