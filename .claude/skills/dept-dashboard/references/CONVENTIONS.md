# Coding Conventions Reference

## Python Conventions

### Imports

Organize imports in three groups, separated by blank lines:

```python
# Standard library
import os
from typing import Optional, List

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Local
from app.config import settings
from app.adapters.base import BaseAdapter
from app.api.deps import require_auth, DepartmentDep
```

### Naming

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `scodoc_adapter.py` |
| Classes | PascalCase | `ScolariteIndicators` |
| Functions | snake_case | `get_indicators()` |
| Variables | snake_case | `total_etudiants` |
| Constants | UPPER_SNAKE_CASE | `CACHE_TTL` |

### Pydantic v2 Patterns

**CRITICAL:** This project uses Pydantic v2. Use the new methods:

```python
# ✅ Correct (Pydantic v2)
data = model.model_dump()
data = model.model_dump(exclude={'password'})
obj = Model.model_validate(data)
json_str = model.model_dump_json()

# ❌ Wrong (Pydantic v1 - will fail)
data = model.dict()  # Removed in v2
obj = Model.parse_obj(data)  # Removed in v2
json_str = model.json()  # Removed in v2
```

### Async/Await

All routes and adapters **must** be async. Never block the event loop.

```python
# ✅ Correct
@router.get("/indicators")
async def get_indicators():
    data = await adapter.fetch_data()
    return data

# ❌ Wrong - blocks event loop
@router.get("/indicators")
def get_indicators():  # Not async
    data = adapter.fetch_data()  # Not awaited
    return data
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict

def calculate_rate(total: int, passed: int) -> float:
    return (passed / total) * 100 if total > 0 else 0.0

async def fetch_students(department: str) -> List[Dict[str, any]]:
    ...
```

### Route Patterns

```python
from fastapi import APIRouter, Depends
from app.api.deps import require_view_scolarite, DepartmentDep, AuthUserDep

router = APIRouter(prefix="/api/scolarite", tags=["Scolarité"])

@router.get("/{department}/indicators")
async def get_indicators(
    department: DepartmentDep,
    user: AuthUserDep = Depends(require_view_scolarite),
) -> ScolariteIndicators:
    """Get scolarité indicators for department."""
    ...
```

### Database Models

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class UserDB(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    cas_login = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255))
    is_active = Column(Boolean, default=False)
    
    # Relationships
    permissions = relationship("UserPermissionDB", back_populates="user")
```

### Pydantic Models

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    cas_login: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    cas_login: str
    email: Optional[str]
    is_active: bool
    
    model_config = {"from_attributes": True}  # For ORM mode
```

## TypeScript/React Conventions

### Imports

```typescript
// React
import { useState, useEffect } from 'react'

// Third-party
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

// Local
import { useAuth } from '@/contexts/AuthContext'
import api from '@/services/api'
import StatCard from '@/components/StatCard'
```

### Naming

| Element | Convention | Example |
|---------|------------|---------|
| Files | PascalCase | `ChartContainer.tsx` |
| Components | PascalCase | `<FilterBar />` |
| Functions | camelCase | `fetchIndicators()` |
| Variables | camelCase | `totalStudents` |
| Hooks | camelCase with `use` | `useScolariteData()` |
| Types/Interfaces | PascalCase | `ScolariteIndicators` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL` |

### Component Patterns

```typescript
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface Props {
  department: string
  year?: number
}

export default function ScolaritePage({ department, year = 2024 }: Props) {
  const [filter, setFilter] = useState<string>('')
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['scolarite', 'indicators', department, year],
    queryFn: () => api.scolarite.getIndicators(department, year),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  })
  
  if (isLoading) return <div>Chargement...</div>
  if (error) return <div>Erreur: {error.message}</div>
  
  return (
    <div className="space-y-4">
      <h1>Scolarité - {department}</h1>
      {/* Content */}
    </div>
  )
}
```

### TanStack Query Pattern

Always use TanStack Query for API calls:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Fetching
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['budget', department, year],
  queryFn: () => api.budget.getAll(department, year),
  staleTime: 5 * 60 * 1000,
})

// Mutations
const queryClient = useQueryClient()
const mutation = useMutation({
  mutationFn: (newBudget) => api.budget.create(department, newBudget),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['budget', department] })
  },
})
```

### API Client Pattern

```typescript
// services/api.ts
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
})

// Add auth interceptor
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.params = { ...config.params, token }
  }
  return config
})

export const scolariteApi = {
  getIndicators: (department: string) => 
    apiClient.get<ScolariteIndicators>(`/scolarite/${department}/indicators`)
      .then(res => res.data),
  
  getStudents: (department: string, filters?: StudentFilters) =>
    apiClient.get(`/scolarite/${department}/students`, { params: filters })
      .then(res => res.data),
}

export default {
  scolarite: scolariteApi,
  budget: budgetApi,
  // ...
}
```

### Type Definitions

```typescript
// types/scolarite.ts
export interface ScolariteIndicators {
  total_etudiants: number
  taux_reussite: number
  taux_presence: number
}

export interface Student {
  id: number
  nom: string
  prenom: string
  email: string
  groupe: string
}

export type StudentFilters = {
  groupe?: string
  annee?: number
  search?: string
}
```

### Permission Checks

```typescript
import { useAuth } from '@/contexts/AuthContext'
import PermissionGate from '@/components/PermissionGate'

function BudgetPage() {
  const { checkPermission, user } = useAuth()
  
  const canEdit = checkPermission('RT', 'can_edit_budget')
  
  return (
    <div>
      {/* Conditional rendering */}
      {canEdit && <button>Modifier</button>}
      
      {/* Permission gate */}
      <PermissionGate department="RT" permission="can_edit_budget">
        <button>Supprimer</button>
      </PermissionGate>
    </div>
  )
}
```

## File Organization

### Backend Route File

```python
"""
Scolarité routes - student data and indicators.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.scolarite import ScolariteIndicators, Student
from app.api.deps import (
    require_view_scolarite,
    require_edit_scolarite,
    DepartmentDep,
    AuthUserDep,
)

router = APIRouter(prefix="/api/scolarite", tags=["Scolarité"])

# Routes...
```

### Frontend Page File

```typescript
/**
 * Scolarité Page
 * Displays student indicators, attendance, and grades
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import api from '@/services/api'

export default function ScolaritePage() {
  // Component code...
}
```

## Error Handling

### Backend

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@router.get("/{department}/data")
async def get_data(department: DepartmentDep):
    try:
        data = await adapter.fetch_data()
        return data
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch data: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Frontend

```typescript
const { data, error } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
})

if (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 403) {
      return <div>Accès refusé</div>
    }
    return <div>Erreur: {error.response?.data?.detail}</div>
  }
  return <div>Erreur: {error.message}</div>
}
```

## Database Operations

### SQLAlchemy Queries

```python
from sqlalchemy.orm import Session
from app.models.db_models import UserDB, BudgetAnnuelDB

# Get one
user = db.query(UserDB).filter(UserDB.cas_login == login).first()

# Get all with filters
budgets = db.query(BudgetAnnuelDB).filter(
    BudgetAnnuelDB.department == department,
    BudgetAnnuelDB.annee == year
).all()

# Create
new_budget = BudgetAnnuelDB(
    department=department,
    annee=year,
    budget_total=100000,
)
db.add(new_budget)
db.commit()
db.refresh(new_budget)

# Update
budget.budget_total = 120000
db.commit()

# Delete
db.delete(budget)
db.commit()
```

### DB-Agnostic Code

Avoid SQLite-specific functions. Use Python-level processing instead:

```python
# ❌ Wrong - SQLite-specific
from sqlalchemy import func
results = db.query(
    func.strftime('%Y-%m', DepenseDB.date_depense).label('month'),
    func.sum(DepenseDB.montant)
).group_by('month').all()

# ✅ Correct - DB-agnostic
from collections import defaultdict

depenses = db.query(DepenseDB).all()
by_month = defaultdict(float)
for d in depenses:
    month = d.date_depense.strftime('%Y-%m')
    by_month[month] += d.montant
```

## Comments and Documentation

### Backend Docstrings

```python
async def calculate_success_rate(department: str, year: int) -> float:
    """
    Calculate the success rate for a department and year.
    
    Args:
        department: Department code (RT, GEII, etc.)
        year: Academic year (2024, 2025, etc.)
    
    Returns:
        Success rate as percentage (0-100)
    
    Raises:
        HTTPException: If department is invalid or no data available
    """
    ...
```

### Frontend JSDoc

```typescript
/**
 * Fetch budget indicators for a department and year
 * @param department - Department code (RT, GEII, etc.)
 * @param year - Academic year
 * @returns Budget indicators data
 */
async function fetchBudgetIndicators(
  department: string,
  year: number
): Promise<BudgetIndicators> {
  ...
}
```

## Code Quality

### Python

- Use `black` for formatting
- Use `isort` for import sorting
- Use `mypy` for type checking
- Use `pylint` for linting

### TypeScript

- Use ESLint for linting
- Use Prettier for formatting
- Enable strict mode in `tsconfig.json`
