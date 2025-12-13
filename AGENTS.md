# AGENTS.md - Instructions pour Agents IA

Ce fichier fournit le contexte et les conventions pour les agents IA travaillant sur ce projet.

## 📋 Vue d'ensemble du projet

**Dept-Dashboard** est un dashboard modulaire pour un département d'enseignement universitaire. Il centralise et visualise les données de plusieurs sources (ScoDoc, Apogée, Parcoursup, fichiers Excel) avec des indicateurs sur :
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
| Backend | FastAPI, Python 3.11+, Pydantic v2, httpx, pandas |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Cache | Redis 7 |
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
│   │   │       └── admin.py
│   │   ├── adapters/            # Pattern adapter pour sources de données
│   │   │   ├── base.py          # Classe abstraite BaseAdapter
│   │   │   ├── scodoc.py        # API ScoDoc
│   │   │   ├── parcoursup.py    # Parsing CSV Parcoursup
│   │   │   └── excel.py         # Lecture fichiers Excel/CSV
│   │   ├── models/              # Modèles Pydantic
│   │   │   ├── scolarite.py
│   │   │   ├── recrutement.py
│   │   │   ├── budget.py
│   │   │   ├── edt.py
│   │   │   └── admin.py
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
│   │   │   └── ExportButton.tsx
│   │   ├── pages/               # Pages du dashboard
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Scolarite.tsx
│   │   │   ├── Recrutement.tsx
│   │   │   ├── Budget.tsx
│   │   │   ├── EDT.tsx
│   │   │   └── Admin.tsx
│   │   ├── services/
│   │   │   └── api.ts           # Client API (fetch wrapper)
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # Types TypeScript
│   └── package.json
├── data/
│   └── examples/                # Fichiers CSV d'exemple
├── docker-compose.yml
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

# Modèles Pydantic : préfixer avec le domaine
class ScolariteIndicators(BaseModel):
    total_etudiants: int
    taux_reussite: float

# Routes : utiliser des routers par domaine
router = APIRouter(prefix="/api/scolarite", tags=["Scolarité"])

@router.get("/indicators")
async def get_indicators() -> ScolariteIndicators:
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
  const { data, isLoading } = useQuery({
    queryKey: ['scolarite'],
    queryFn: () => api.scolarite.getIndicators()
  });
  
  if (isLoading) return <Loading />;
  return <div>...</div>;
}

// API calls : centralisés dans services/api.ts
export const scolariteApi = {
  getIndicators: () => fetchApi<ScolariteData>('/api/scolarite/indicators'),
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
data = await cache_service.get(CacheKeys.SCOLARITE_INDICATORS)
if not data:
    data = await adapter.fetch_data()
    await cache_service.set(CacheKeys.SCOLARITE_INDICATORS, data, ttl=3600)
```

### 3. Pattern API Frontend

```typescript
// Toujours utiliser TanStack Query pour le data fetching
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['domain', 'resource', params],
  queryFn: () => api.domain.getResource(params),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

## 🧪 Tests

### Lancer les tests backend

```bash
cd backend
pytest -v                    # Tous les tests
pytest tests/test_routes.py  # Tests routes uniquement
pytest --cov=app             # Avec couverture
```

### Structure des tests

```python
# tests/test_routes.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_scolarite_indicators(client: AsyncClient):
    response = await client.get("/api/scolarite/indicators")
    assert response.status_code == 200
    data = response.json()
    assert "total_etudiants" in data
```

## 🚀 Commandes utiles

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

## 🔗 Ressources

- [Plan de projet détaillé](plan.md)
- [ScoDoc API Documentation](https://scodoc.org/ScoDoc9API/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Recharts Documentation](https://recharts.org/)
- [TanStack Query](https://tanstack.com/query/latest)

## 📊 État du projet

Voir [plan.md](plan.md) pour la roadmap complète et le journal des modifications.

### Fonctionnalités implémentées
- ✅ Backend API complet (4 domaines + admin)
- ✅ Frontend avec graphiques Recharts
- ✅ Cache Redis + Scheduler
- ✅ Filtres avancés
- ✅ Export PDF/PNG/SVG
- ✅ Tests unitaires
- ✅ Documentation OpenAPI

### À faire
- [ ] Authentification JWT/CAS
- [ ] Connexion réelle API ScoDoc
- [ ] Upload fichiers via interface
