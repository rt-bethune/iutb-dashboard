# Architecture Reference

## System Overview

```
Frontend (React/Vite/TS) → FastAPI Backend → Adapters → Data Sources
                              ↓
                    SQLite/PostgreSQL (users) + Redis (cache)
```

## Backend Structure

```
backend/app/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic Settings (env vars)
├── database.py          # SQLAlchemy setup
├── api/
│   ├── deps.py          # Auth & permission dependencies
│   └── routes/          # Domain routes
│       ├── scolarite.py
│       ├── recrutement.py
│       ├── budget.py
│       ├── edt.py
│       ├── auth.py
│       ├── upload.py
│       └── *_admin.py   # CRUD admin routes
├── adapters/            # Data source connectors
│   ├── base.py          # BaseAdapter abstract class
│   ├── scodoc.py        # ScoDoc API
│   ├── parcoursup.py    # CSV parser
│   ├── cas.py           # CAS authentication
│   └── excel.py         # Excel/CSV reader
├── models/              # Pydantic + SQLAlchemy models
│   ├── db_models.py     # Database tables (SQLAlchemy)
│   └── *.py             # Response models (Pydantic)
├── crud/                # Database operations
├── schemas/             # Pydantic validation schemas
└── services/
    ├── cache.py         # Redis cache service
    └── scheduler.py     # APScheduler jobs
```

## Frontend Structure

```
frontend/src/
├── App.tsx              # Routes & layout
├── main.tsx             # Entry point
├── components/          # Reusable UI components
│   ├── Layout.tsx       # Navigation & header
│   ├── PermissionGate.tsx
│   └── FilterBar.tsx
├── contexts/
│   ├── AuthContext.tsx  # Auth state management
│   └── DepartmentContext.tsx
├── pages/               # Route pages
│   ├── Dashboard.tsx
│   ├── Budget.tsx
│   ├── Recrutement.tsx
│   ├── Login.tsx
│   └── Admin*.tsx
├── services/
│   └── api.ts           # API client (axios)
└── types/               # TypeScript types
```

## Database Schema

### Authentication Tables

```
user
├── id (PK)
├── cas_login (unique)
├── email
├── nom, prenom
├── is_active
├── is_superadmin
└── created_at

user_permission
├── id (PK)
├── user_id (FK → user)
├── department (RT, GEII, GCCD, GMP, QLIO, CHIMIE)
├── can_view_scolarite, can_edit_scolarite
├── can_view_recrutement, can_edit_recrutement
├── can_view_budget, can_edit_budget
├── can_view_edt, can_edit_edt
├── can_import, can_export
└── is_dept_admin
```

### Budget Tables

```
budget_annuel
├── id (PK)
├── department
├── annee
├── budget_total
└── created_at

ligne_budget
├── id (PK)
├── budget_annuel_id (FK)
├── categorie (Personnel, Fonctionnement, Investissement)
├── budget_initial
├── budget_engage
└── budget_paye

depense
├── id (PK)
├── budget_annuel_id (FK)
├── libelle
├── montant
├── categorie
├── date_depense
├── fournisseur
└── statut
```

### Recruitment Tables

```
campagne_recrutement
├── id (PK)
├── department
├── annee
├── nb_places
├── rang_dernier_appele
└── taux_remplissage

candidat
├── id (PK)
├── campagne_id (FK)
├── type_bac (General, Techno, Pro)
├── mention (TB, B, AB, Passable)
├── departement_origine
├── lycee
├── statut (En attente, Accepté, Refusé)
└── rang_classement

stats_parcoursup
├── id (PK)
├── department
├── annee
├── nb_voeux
├── nb_admis
├── nb_acceptes
└── par_type_bac (JSON)
```

## Adapter Pattern

All data source adapters inherit from `BaseAdapter`:

```python
# app/adapters/base.py
class BaseAdapter(ABC):
    @abstractmethod
    async def fetch_data(self) -> dict:
        """Fetch data from source."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is available."""
        pass
```

**Implementations:**
- `ScoDocAdapter` - REST API calls to ScoDoc
- `ParcoursupAdapter` - CSV file parsing
- `ExcelAdapter` - Excel/CSV reading
- `CASAdapter` - CAS authentication flow

## Cache Strategy

Redis cache with TTL per domain:

```python
# Read with fallback
data = await cache_service.get(CacheKeys.SCOLARITE_INDICATORS)
if not data:
    data = await adapter.fetch_data()
    await cache_service.set(CacheKeys.SCOLARITE_INDICATORS, data, ttl=3600)
```

**Cache keys:** `{domain}:{department}:{resource}`
**TTL:** 1 hour for indicators, 30 min for lists
**Refresh:** Query param `?refresh=true` forces refresh

## Authentication Flow

1. User clicks "Se connecter"
2. Frontend redirects to `/api/auth/login?return_url={frontend_url}`
3. Backend redirects to CAS server
4. CAS authenticates user, redirects to `/api/auth/cas/callback?ticket={ticket}`
5. Backend validates ticket with CAS
6. Backend creates/updates user in DB, generates JWT
7. Backend redirects to frontend with `?token={jwt}`
8. Frontend stores token in localStorage
9. Frontend fetches user with `/api/auth/me?token={jwt}`

**Dev mode:** Set `CAS_USE_MOCK=true`, use dev login form with any username.
