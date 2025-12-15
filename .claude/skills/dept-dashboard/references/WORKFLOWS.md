# Development Workflows

## Adding a New Indicator

**Example:** Add "taux_abandon" (dropout rate) to scolarite indicators.

### 1. Backend Model

```python
# app/models/scolarite.py
class ScolariteIndicators(BaseModel):
    total_etudiants: int
    taux_reussite: float
    taux_abandon: float  # NEW
```

### 2. Backend Route

```python
# app/api/routes/scolarite.py
@router.get("/{department}/indicators")
async def get_indicators(department: DepartmentDep, ...):
    data = await adapter.fetch_data()
    
    return ScolariteIndicators(
        total_etudiants=data['total'],
        taux_reussite=data['reussite'],
        taux_abandon=calculate_dropout_rate(data),  # NEW
    )
```

### 3. Frontend Type

```typescript
// frontend/src/types/scolarite.ts
export interface ScolariteIndicators {
  total_etudiants: number
  taux_reussite: number
  taux_abandon: number  // NEW
}
```

### 4. Frontend Display

```typescript
// frontend/src/pages/Scolarite.tsx
<StatCard
  title="Taux d'abandon"
  value={`${data.taux_abandon.toFixed(1)}%`}
  icon={<AlertCircle />}
/>
```

## Adding a New Page

**Example:** Add a "Stages" (internships) page.

### 1. Create Page Component

```typescript
// frontend/src/pages/Stages.tsx
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'

export default function StagesPage() {
  const { department } = useDepartment()
  const { checkPermission } = useAuth()
  
  const canView = checkPermission(department, 'can_view_stages')
  
  if (!canView) {
    return <div>Accès refusé</div>
  }
  
  return <div>Stages content</div>
}
```

### 2. Add Route

```typescript
// frontend/src/App.tsx
import StagesPage from './pages/Stages'

<Route path="/stages" element={
  <ProtectedRoute>
    <StagesPage />
  </ProtectedRoute>
} />
```

### 3. Add Navigation Link

```typescript
// frontend/src/components/Layout.tsx
const navItems = [
  // ... existing items
  { path: '/stages', label: 'Stages', icon: Briefcase }
]

// Filter by permission
{navItems.filter(item => 
  checkPermission(department, `can_view_${item.path.slice(1)}`)
).map(item => ...)}
```

### 4. Create Backend Route

```python
# backend/app/api/routes/stages.py
from fastapi import APIRouter, Depends
from app.api.deps import require_view_stages, DepartmentDep

router = APIRouter(prefix="/api/stages", tags=["Stages"])

@router.get("/{department}/indicators")
async def get_indicators(
    department: DepartmentDep,
    user = Depends(require_view_stages),
):
    return {"total_stages": 0}
```

### 5. Register Route

```python
# backend/app/main.py
from app.api.routes import stages

app.include_router(stages.router)
```

### 6. Add Permissions

See [PERMISSIONS.md](PERMISSIONS.md) for adding new permissions.

## Adding a New Data Adapter

**Example:** Add an adapter for fetching data from Apogée.

### 1. Create Adapter

```python
# backend/app/adapters/apogee.py
from app.adapters.base import BaseAdapter
import httpx

class ApogeeAdapter(BaseAdapter):
    def __init__(self, base_url: str, api_key: str, department: str):
        self.base_url = base_url
        self.api_key = api_key
        self.department = department
    
    async def fetch_data(self) -> dict:
        """Fetch student data from Apogée."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/students",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"department": self.department}
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if Apogée API is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
```

### 2. Add Config

```python
# backend/app/config.py
class Settings(BaseSettings):
    # ... existing config
    apogee_base_url: str = ""
    apogee_api_key: str = ""
```

### 3. Create Dependency

```python
# backend/app/api/deps.py
@lru_cache
def get_apogee_adapter() -> ApogeeAdapter:
    settings = get_settings()
    return ApogeeAdapter(
        base_url=settings.apogee_base_url,
        api_key=settings.apogee_api_key,
        department=settings.scodoc_department,
    )

ApogeeDep = Annotated[ApogeeAdapter, Depends(get_apogee_adapter)]
```

### 4. Use in Route

```python
# backend/app/api/routes/scolarite.py
@router.get("/{department}/apogee-data")
async def get_apogee_data(
    department: DepartmentDep,
    adapter: ApogeeAdapter = Depends(get_apogee_adapter_for_department),
    user = Depends(require_view_scolarite),
):
    data = await adapter.fetch_data()
    return data
```

### 5. Add to Cache Scheduler (Optional)

```python
# backend/app/services/scheduler.py
async def refresh_apogee_cache():
    adapter = get_apogee_adapter()
    data = await adapter.fetch_data()
    await cache_service.set(CacheKeys.APOGEE_DATA, data, ttl=3600)

scheduler.add_job(
    refresh_apogee_cache,
    'interval',
    hours=1,
    id='refresh_apogee'
)
```

## Testing Workflows

### Backend Unit Tests

```python
# tests/test_routes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_scolarite_indicators(client: AsyncClient):
    response = await client.get("/api/scolarite/RT/indicators")
    assert response.status_code == 200
    data = response.json()
    assert "total_etudiants" in data
    assert "taux_reussite" in data
```

### Run Tests

```bash
cd backend
pytest -v                    # All tests
pytest tests/test_routes.py  # Specific file
pytest --cov=app            # With coverage
```

### Frontend Testing

Use the browser dev tools and check API calls:

1. Open Network tab
2. Trigger action
3. Verify request/response
4. Check for errors in console

## Database Workflow

### Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Add new column"
```

### Review Migration

Check generated file in `backend/alembic/versions/`, edit if needed.

### Apply Migration

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1  # Go back one version
alembic downgrade base  # Reset to empty DB
```

### Check Status

```bash
alembic current  # Current version
alembic history  # All versions
```

## Upload File Workflow

**Example:** Upload and process Parcoursup CSV.

### 1. Frontend Upload

```typescript
// frontend/src/pages/Upload.tsx
const uploadFile = async (file: File, type: string) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.upload.uploadFile(department, type, formData)
  return response.data
}
```

### 2. Backend Route

```python
# backend/app/api/routes/upload.py
from fastapi import UploadFile, File

@router.post("/{department}/parcoursup")
async def upload_parcoursup(
    department: DepartmentDep,
    file: UploadFile = File(...),
    user = Depends(require_import),
):
    # Save file
    file_path = f"uploads/parcoursup/{department}_{timestamp}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Process with adapter
    adapter = get_parcoursup_adapter()
    data = await adapter.parse_csv(file_path, department)
    
    # Store in DB
    await store_parcoursup_data(data, department)
    
    return {"status": "success", "rows": len(data)}
```

## Debugging Workflows

### Backend Logs

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Fetching data for department: {department}")
logger.warning(f"Cache miss for key: {cache_key}")
logger.error(f"Failed to fetch data: {e}")
```

### Frontend Logs

```typescript
console.log('Fetching indicators for', department)
console.error('API call failed:', error)
```

### Check Redis Cache

```bash
docker-compose exec redis redis-cli
> KEYS *
> GET scolarite:RT:indicators
> DEL scolarite:RT:indicators  # Clear cache
```

### Check Database

```bash
docker-compose exec db psql -U dashboard dept_dashboard
> SELECT * FROM "user" LIMIT 5;
> SELECT * FROM user_permission WHERE department = 'RT';
```

## Environment Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Backend
DEBUG=true
CAS_USE_MOCK=true
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./data/dashboard.db
REDIS_URL=redis://localhost:6379

# Frontend (via Vite)
VITE_API_URL=http://localhost:8000
```
