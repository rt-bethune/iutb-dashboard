# Permission System Reference

## Permission Model

Permissions are **department-scoped**. Each user can have different permissions for different departments.

**Departments:** RT, GEII, GCCD, GMP, QLIO, CHIMIE

**Domains:** scolarite, recrutement, budget, edt

**Actions:** view, edit

**Special permissions:** import, export, is_dept_admin

**Superadmin:** Has all permissions across all departments.

## Backend Route Protection

### Basic Pattern

```python
from app.api.deps import require_view_budget, require_edit_budget, DepartmentDep, AuthUserDep

@router.get("/{department}/indicators")
async def get_indicators(
    department: DepartmentDep,
    user: AuthUserDep = Depends(require_view_budget),
):
    """Requires view_budget permission for the specified department."""
    ...

@router.post("/{department}/")
async def create_budget(
    department: DepartmentDep,
    user: AuthUserDep = Depends(require_edit_budget),
):
    """Requires edit_budget permission for the specified department."""
    ...
```

### Permission Dependencies

Pre-built dependencies in `app/api/deps.py`:

```python
# View permissions
require_view_scolarite
require_view_recrutement
require_view_budget
require_view_edt

# Edit permissions
require_edit_scolarite
require_edit_recrutement
require_edit_budget
require_edit_edt

# Special permissions
require_import  # Can upload data
require_export  # Can export data
```

### Custom Permission Checks

```python
from app.api.deps import check_permission, require_auth, DepartmentDep
from app.database import get_db

@router.get("/{department}/custom")
async def custom_endpoint(
    department: DepartmentDep,
    user: AuthUserDep = Depends(require_auth),
    db: Session = Depends(get_db),
):
    # Manual permission check
    if not check_permission(user, department, "budget", "view", db):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    ...
```

### Creating New Permission Checkers

```python
from app.api.deps import PermissionChecker

# Create a custom permission dependency
require_view_custom = PermissionChecker("custom_domain", "view")

@router.get("/{department}/custom")
async def get_custom(
    department: DepartmentDep,
    user: AuthUserDep = Depends(require_view_custom),
):
    ...
```

## Frontend Permission Checks

### Using AuthContext

```typescript
import { useAuth } from '@/contexts/AuthContext'

function BudgetPage() {
  const { checkPermission, isAdmin } = useAuth()
  
  // Check specific permission
  const canViewBudget = checkPermission('RT', 'can_view_budget')
  const canEditBudget = checkPermission('RT', 'can_edit_budget')
  
  // Check if admin
  const isRTAdmin = isAdmin('RT')
  const isAnyAdmin = isAdmin()  // Admin of any department
  
  if (!canViewBudget) {
    return <div>Accès refusé</div>
  }
  
  return (
    <div>
      {/* Read-only view */}
      {canEditBudget && (
        <button>Modifier</button>
      )}
    </div>
  )
}
```

### PermissionGate Component

```typescript
import PermissionGate from '@/components/PermissionGate'

function BudgetPage() {
  return (
    <div>
      <PermissionGate
        department="RT"
        permission="can_view_budget"
        fallback={<div>Accès refusé</div>}
      >
        {/* Protected content */}
      </PermissionGate>
      
      <PermissionGate
        department="RT"
        permission="can_edit_budget"
      >
        <button>Modifier</button>
      </PermissionGate>
    </div>
  )
}
```

### Filtering Navigation

```typescript
// Layout.tsx
const navItems = [
  { 
    path: '/scolarite', 
    label: 'Scolarité',
    checkPermission: (dept: string) => checkPermission(dept, 'can_view_scolarite')
  },
  { 
    path: '/budget', 
    label: 'Budget',
    checkPermission: (dept: string) => checkPermission(dept, 'can_view_budget')
  },
]

// Filter nav items based on user permissions for current department
const visibleNavItems = navItems.filter(item => 
  item.checkPermission(currentDepartment)
)
```

## Permission Database Structure

### UserPermissionDB Model

```python
class UserPermissionDB(Base):
    __tablename__ = "user_permission"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    department = Column(String(10), nullable=False)
    
    # Domain permissions
    can_view_scolarite = Column(Boolean, default=False)
    can_edit_scolarite = Column(Boolean, default=False)
    can_view_recrutement = Column(Boolean, default=False)
    can_edit_recrutement = Column(Boolean, default=False)
    can_view_budget = Column(Boolean, default=False)
    can_edit_budget = Column(Boolean, default=False)
    can_view_edt = Column(Boolean, default=False)
    can_edit_edt = Column(Boolean, default=False)
    
    # Special permissions
    can_import = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)
    is_dept_admin = Column(Boolean, default=False)
```

### User Response with Permissions

```python
class UserResponse(BaseModel):
    id: int
    cas_login: str
    email: Optional[str]
    nom: Optional[str]
    prenom: Optional[str]
    is_active: bool
    is_superadmin: bool
    permissions: dict[str, DepartmentPermissions]
```

## Adding New Permissions

### 1. Database Migration

```python
# alembic/versions/xxx_add_new_permission.py
def upgrade():
    op.add_column('user_permission', sa.Column('can_view_new_domain', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permission', sa.Column('can_edit_new_domain', sa.Boolean(), nullable=False, server_default='false'))
```

### 2. Update DB Model

```python
# app/models/db_models.py
class UserPermissionDB(Base):
    # ... existing columns ...
    can_view_new_domain = Column(Boolean, default=False)
    can_edit_new_domain = Column(Boolean, default=False)
```

### 3. Update Pydantic Model

```python
# app/models/admin.py
class DepartmentPermissions(BaseModel):
    # ... existing fields ...
    can_view_new_domain: bool = False
    can_edit_new_domain: bool = False
```

### 4. Create Permission Dependencies

```python
# app/api/deps.py
require_view_new_domain = PermissionChecker("new_domain", "view")
require_edit_new_domain = PermissionChecker("new_domain", "edit")
```

### 5. Update Frontend Type

```typescript
// frontend/src/contexts/AuthContext.tsx
interface DepartmentPermissions {
  // ... existing permissions ...
  can_view_new_domain: boolean
  can_edit_new_domain: boolean
}
```

## Common Permission Patterns

### Read-only users

Give view permissions only, no edit/import/export.

### Department secretary

All view permissions + edit for scolarite/recrutement, import/export for their department.

### Department admin

Set `is_dept_admin: true` → grants all permissions for that department.

### Superadmin

Set `is_superadmin: true` on user → grants all permissions across all departments.

## Handling 403 Errors

```typescript
// Frontend API interceptor
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403) {
      // Show permission denied message
      toast.error('Vous n\'avez pas la permission d\'accéder à cette ressource')
    }
    return Promise.reject(error)
  }
)
```
