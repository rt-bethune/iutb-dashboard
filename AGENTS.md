# AGENTS.md - Instructions pour Agents IA

Ce fichier fournit le contexte et les conventions pour les agents IA travaillant sur ce projet.

## 📋 Vue d'ensemble du projet

**Dept-Dashboard** est un dashboard modulaire pour un département d'enseignement universitaire. Il centralise et visualise les données de plusieurs sources (ScoDoc, Parcoursup, fichiers Excel — Apogée envisagé) avec des indicateurs sur :
- **Scolarité** : effectifs, notes, taux de réussite
- **Recrutement** : candidatures Parcoursup, admissions
- **Budget** : dépenses, allocations par catégorie
- **EDT** : charges enseignantes, occupation salles

## 🏗️ Architecture

```
Frontend (React/Vite) ──► API FastAPI ──► Adapters ──► Sources de données
                              │
                           Redis (Cache)
```

### Stack technique

| Couche | Technologies |
|--------|-------------|
| Backend | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy, httpx, pandas |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Cache | Redis 7 |
| Migrations | Alembic |
| Scheduler | APScheduler |
| Tests | pytest, pytest-asyncio |
| Déploiement | Docker, docker-compose |

## 📁 Structure du projet

```
Dept-Dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   ├── config.py            # Configuration (Settings Pydantic)
│   │   ├── api/
│   │   │   ├── deps.py          # Dépendances FastAPI
│   │   │   └── routes/          # Routes par domaine
│   │   │       ├── scolarite.py
│   │   │       ├── recrutement.py
│   │   │       ├── budget.py
│   │   │       ├── edt.py
│   │   │       ├── upload.py
│   │   │       ├── budget_admin.py
│   │   │       ├── recrutement_admin.py
│   │   │       ├── admin.py
│   │   │       ├── auth.py
│   │   │       └── users.py
│   │   ├── adapters/            # Pattern adapter pour sources de données
│   │   │   ├── base.py          # Classe abstraite BaseAdapter
│   │   │   ├── scodoc.py        # API ScoDoc
│   │   │   ├── parcoursup.py    # Parsing CSV Parcoursup
│   │   │   └── excel.py         # Lecture fichiers Excel/CSV
│   │   ├── models/              # Modèles Pydantic + SQLAlchemy
│   │   │   ├── db_models.py     # Modèles SQLAlchemy (tables DB)
│   │   │   ├── scolarite.py
│   │   │   ├── recrutement.py
│   │   │   ├── budget.py
│   │   │   ├── edt.py
│   │   │   └── admin.py
│   │   ├── crud/                # Opérations CRUD par domaine
│   │   │   ├── budget.py
│   │   │   └── admin_crud.py
│   │   ├── seeds.py             # Données de démonstration
│   │   └── services/
│   │       ├── cache.py         # Service Redis
│   │       └── scheduler.py     # APScheduler jobs
│   ├── tests/                   # Tests pytest
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Composants réutilisables
│   │   │   ├── Layout.tsx
│   │   │   ├── ChartContainer.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── ExportButton.tsx
│   │   │   ├── PermissionGate.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── pages/               # Pages du dashboard
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Scolarite.tsx
│   │   │   ├── Recrutement.tsx
│   │   │   ├── Budget.tsx
│   │   │   ├── EDT.tsx
│   │   │   ├── Upload.tsx
│   │   │   ├── Admin.tsx
│   │   │   ├── AdminBudget.tsx
│   │   │   ├── AdminRecrutement.tsx
│   │   │   ├── UsersManagement.tsx
│   │   │   ├── Login.tsx
│   │   │   └── PendingValidation.tsx
│   │   ├── services/
│   │   │   └── api.ts           # Client API (fetch wrapper)
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # Types TypeScript
│   └── package.json
├── backend/
│   ├── alembic/                 # Migrations de base de données
│   │   └── versions/            # Fichiers de migration
│   └── alembic.ini              # Configuration Alembic
├── data/
│   └── examples/                # Fichiers CSV d'exemple
├── docker-compose.yml           # Développement
├── docker-compose.prod.yml      # Production
├── .env.prod.example            # Template variables production
├── DEPLOY.md                    # Guide de déploiement
├── plan.md                      # Plan de projet détaillé
└── AGENTS.md                    # Ce fichier
```

## 🔧 Conventions de code

### Backend (Python)

```python
# Imports : stdlib, third-party, local (séparés par ligne vide)
import os
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.adapters.base import BaseAdapter
from app.api.deps import DepartmentDep, require_view_scolarite
from app.models.db_models import UserDB

# Modèles Pydantic : préfixer avec le domaine
class ScolariteIndicators(BaseModel):
    total_etudiants: int
    taux_reussite: float

# Routes : router par domaine, préfixé dans app.main avec /api/{department}/...
router = APIRouter(tags=["Scolarité"])

@router.get("/indicators")
async def get_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
) -> ScolariteIndicators:
    ...

# Adapters : hériter de BaseAdapter
class ScoDocAdapter(BaseAdapter):
    async def fetch_data(self) -> dict:
        ...
```

### Frontend (TypeScript/React)

```typescript
// Types : définir dans types/ ou inline
interface ScolariteData {
  totalEtudiants: number;
  tauxReussite: number;
}

// Composants : functional components avec hooks
export function ScolaritePage() {
  const { department } = useDepartment();

  const { data, isLoading } = useQuery({
    queryKey: ['scolarite', department],
    queryFn: () => scolariteApi.getIndicators(department)
  });
  
  if (isLoading) return <Loading />;
  return <div>...</div>;
}

// API calls : centralisés dans services/api.ts
export const scolariteApi = {
  getIndicators: (department: string) => fetchApi<ScolariteData>(`/api/${department}/scolarite/indicators`),
};
```

### Nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| Fichiers Python | snake_case | `scodoc_adapter.py` |
| Fichiers React | PascalCase | `ChartContainer.tsx` |
| Classes Python | PascalCase | `ScolariteIndicators` |
| Fonctions Python | snake_case | `get_indicators()` |
| Variables Python | snake_case | `total_etudiants` |
| Composants React | PascalCase | `<FilterBar />` |
| Hooks React | camelCase avec `use` | `useScolariteData()` |

## 🗄️ Patterns importants

### 1. Pattern Adapter (Backend)

Tous les adapters héritent de `BaseAdapter` :

```python
# app/adapters/base.py
class BaseAdapter(ABC):
    @abstractmethod
    async def fetch_data(self) -> dict:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

Pour ajouter une nouvelle source de données :
1. Créer `app/adapters/nouveau_adapter.py`
2. Hériter de `BaseAdapter`
3. Implémenter `fetch_data()` et `health_check()`

### 2. Pattern Cache (Redis)

```python
from app.services.cache import cache_service, CacheKeys

# Lecture avec fallback
data = await cache_service.get(CacheKeys.scolarite_indicators(annee, department))
if not data:
    data = await adapter.get_data(annee=annee)
    await cache_service.set(CacheKeys.scolarite_indicators(annee, department), data, ttl=3600)
```

### 3. Pattern API Frontend

```typescript
// Toujours utiliser TanStack Query pour le data fetching
const { department } = useDepartment();

const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['domain', department, 'resource', params],
  queryFn: () => api.domain.getResource(department, params),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

## 🗄️ Base de données

### Schéma des tables

```
┌──────────────────┐     ┌─────────────────────┐
│      user        │────▶│   user_permission   │
├──────────────────┤     ├─────────────────────┤
│ id               │     │ id                  │
│ cas_login        │     │ user_id (FK)        │
│ email, nom       │     │ department          │
│ is_active        │     │ can_view_*          │
│ is_superadmin    │     │ can_edit_*          │
└──────────────────┘     │ is_dept_admin       │
                         └─────────────────────┘

┌──────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  budget_annuel   │────▶│    ligne_budget     │     │     depense     │
├──────────────────┤     ├─────────────────────┤     ├─────────────────┤
│ id               │     │ id                  │     │ id              │
│ department       │     │ budget_annuel_id    │     │ budget_annuel_id│
│ annee            │     │ categorie           │     │ libelle, montant│
│ budget_total     │     │ budget_initial      │     │ categorie, date │
└──────────────────┘     │ engage, paye        │     │ fournisseur     │
                         └─────────────────────┘     └─────────────────┘

┌────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│campagne_recrutement│────▶│      candidat       │     │ stats_parcoursup  │
├────────────────────┤     ├─────────────────────┤     ├───────────────────┤
│ id                 │     │ id                  │     │ id                │
│ department         │     │ campagne_id (FK)    │     │ department, annee │
│ annee              │     │ type_bac, mention   │     │ nb_voeux          │
│ nb_places          │     │ departement_origine │     │ nb_acceptes       │
│ rang_dernier_appele│     │ lycee, statut       │     │ par_type_bac (JSON│
└────────────────────┘     └─────────────────────┘     └───────────────────┘
```

### Migrations Alembic

```bash
# Appliquer les migrations
cd backend && alembic upgrade head

# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Voir l'état
alembic current
alembic history
```

### Seeding des données

```bash
# Seed les données de démo (users, budget, recrutement)
python -m app.seeds

# Force reseed (supprime les données existantes)
python -m app.seeds --force

# Via API
curl -X POST "http://localhost:8000/api/admin/seed?force=true"
```

## 🧪 Tests

### Lancer les tests backend

```bash
cd backend
pytest -v                    # Tous les tests
pytest tests/test_routes.py  # Tests routes uniquement
pytest --cov=app             # Avec couverture
```

Les routes métiers exigent un JWT et des permissions. En tests d'intégration, générez un token via `/api/auth/dev/login?username=admin` (CAS mock) ou override les dépendances `require_*` si besoin.

### Structure des tests

```python
# tests/test_routes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_scolarite_indicators(client: AsyncClient):
    token = "DEV_TOKEN"  # récupéré via /api/auth/dev/login?username=admin
    response = await client.get(
        "/api/RT/scolarite/indicators",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_etudiants" in data
```

## 🚀 Commandes utiles

### Environnement virtuel Python

Le backend utilise un virtualenv situé dans `backend/venv/` (pas `.venv`).

```bash
# Activer l'environnement
source backend/venv/bin/activate

# Ou utiliser directement le Python du venv
backend/venv/bin/python -m <module>

# Lancer uvicorn avec le bon Python
backend/venv/bin/python -m uvicorn app.main:app --reload --port 8000 --app-dir backend
```

### Développement

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Docker (tout ensemble)
docker-compose up --build
```

### Production

```bash
docker-compose -f docker-compose.yml up -d
```

## 📝 Tâches courantes

### Ajouter un nouvel indicateur

1. **Backend** : Ajouter le champ dans le modèle Pydantic (`app/models/`)
2. **Backend** : Calculer la valeur dans l'adapter ou la route
3. **Frontend** : Ajouter le type TypeScript
4. **Frontend** : Afficher dans le composant approprié

### Ajouter une nouvelle source de données

1. Créer l'adapter dans `app/adapters/`
2. Ajouter la configuration dans `app/config.py`
3. Créer/modifier les routes dans `app/api/routes/`
4. Ajouter les jobs de cache dans `app/services/scheduler.py`

### Ajouter une nouvelle page

1. Créer la page dans `frontend/src/pages/`
2. Ajouter la route dans `App.tsx`
3. Ajouter le lien dans `Layout.tsx`
4. Créer les appels API dans `services/api.ts`

## ⚠️ Points d'attention

1. **Pydantic v2** : Utiliser `model_dump()` au lieu de `.dict()`, `model_validate()` au lieu de `parse_obj()`

2. **Async/Await** : Toutes les routes et adapters sont async. Ne pas bloquer l'event loop.

3. **Cache Redis** : Toujours définir un TTL. Utiliser `?refresh=true` pour forcer le refresh.

4. **Types TypeScript** : Maintenir la cohérence avec les modèles Pydantic backend.

5. **Fichiers CSV** : Encoding UTF-8, séparateur `;` pour les fichiers français.

6. **Auth & permissions** : Les routes métier attendent un header `Authorization: Bearer <token>` et vérifient les permissions du département ; override les dépendances `require_*` en test si nécessaire.

## 🔗 Ressources

- [Plan de projet détaillé](plan.md)
- [ScoDoc API Documentation](https://scodoc.org/ScoDoc9API/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Recharts Documentation](https://recharts.org/)
- [TanStack Query](https://tanstack.com/query/latest)

## 📊 État du projet

Voir [plan.md](plan.md) pour la roadmap complète et le journal des modifications.

### Fonctionnalités implémentées
- ✅ Routes API scindées par département + client React `DepartmentContext`
- ✅ Auth CAS (mock) + JWT, garde frontend, pages Login/PendingValidation
- ✅ Gestion utilisateurs/permissions multi-départements + pages Admin/Users
- ✅ Admin budget/recrutement (CRUD + imports), upload multi-types par département
- ✅ Dashboards frontend (Recharts, filtres, exports) et cache Redis + scheduler
- ✅ Seeds démo, migrations Alembic initiales, tests backend et documentation OpenAPI

### À faire
- [ ] Valider la connexion ScoDoc avec de vraies données (perf, erreurs réseau)
- [ ] Durcir la config de production (HTTPS/nginx, variables secrètes, monitoring)
- [ ] Ajouter alerting/suivi sur les jobs et le cache
