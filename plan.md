# Dashboard Département - Plan de Projet

## 📋 Vue d'ensemble

Dashboard modulaire pour un département d'enseignement permettant de centraliser et visualiser les données de plusieurs sources (ScoDoc, Parcoursup, fichiers Excel — Apogée envisagé) avec des indicateurs sur la scolarité, le recrutement, le budget et les emplois du temps.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│        Frontend React + Vite + Tailwind + Recharts     │
│  Auth (CAS/JWT), context département, pages métier     │
└───────────────────────┬────────────────────────────────┘
                        │ REST API
┌───────────────────────▼────────────────────────────────┐
│             API d'Agrégation (FastAPI)                 │
│  /api/{dept}/scolarite · /recrutement · /budget · /edt │
└───────────────────────┬────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────┐
│             Couche Adapters (Pattern Plugin)           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ ScoDoc  │ │ Parcoursup│ │  Excel   │ │  (mock)    │  │
│  │Adapter  │ │ Adapter  │ │ Adapter  │ │  sources   │  │
│  └─────────┘ └──────────┘ └──────────┘ └────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 📊 Domaines et Indicateurs

### 1. Scolarité (ScoDoc principal)
- Nombre total d'étudiants par formation/semestre
- Taux de réussite par UE/module
- Moyennes générales et distribution des notes
- Taux d'absentéisme
- Évolution année par année

### 2. Recrutement (Parcoursup + fichiers)
- Nombre de candidatures reçues
- Taux d'acceptation / confirmation
- Origine géographique des candidats
- Type de bac des admis
- Évolution des vœux sur plusieurs années

### 3. Budget (fichiers Excel)
- Budget alloué vs dépensé
- Répartition par catégorie (fonctionnement, investissement)
- Suivi des commandes
- Prévisionnel vs réalisé

### 4. EDT / Charges (fichiers Excel/ADE)
- Volume horaire par enseignant
- Taux d'occupation des salles
- Répartition CM/TD/TP
- Heures complémentaires

---

## 🛠️ Stack Technique

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Validation**: Pydantic v2
- **HTTP Client**: httpx (async)
- **Data Processing**: pandas, openpyxl
- **Base de données**: PostgreSQL (optionnel, pour cache)
- **Auth**: JWT / python-jose

### Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **UI Components**: Tailwind CSS + composants maison (Lucide, tables, cards)
- **Charts**: Recharts
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router

---

## 📁 Structure du Projet

```
Dept-Dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   ├── config.py            # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # Dépendances communes
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── scolarite.py
│   │   │       ├── recrutement.py
│   │   │       ├── budget.py
│   │   │       └── edt.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Classe abstraite
│   │   │   ├── scodoc.py
│   │   │   ├── apogee.py
│   │   │   ├── parcoursup.py
│   │   │   └── excel.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── scolarite.py
│   │   │   ├── recrutement.py
│   │   │   ├── budget.py
│   │   │   └── edt.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── aggregator.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── plan.md
└── README.md
```

---

## 📅 Roadmap

### Phase 1 - Fondations ✅ Terminée
- [x] Définir l'architecture
- [x] Créer le plan de projet
- [x] Initialiser le backend FastAPI
- [x] Créer la couche abstraite des adapters
- [x] Implémenter l'adapter ScoDoc (mock)
- [x] Implémenter l'adapter Parcoursup (mock + parsing)
- [x] Implémenter l'adapter Excel (budget + EDT)
- [x] Créer les routes API de base (4 domaines)
- [x] Initialiser le frontend React/Vite
- [x] Créer les composants de base du dashboard
- [x] Créer les pages avec graphiques (Dashboard, Scolarité, Recrutement, Budget, EDT)

### Phase 2 - Adapters & Data ✅ Terminée
- [x] Adapter Excel/CSV fonctionnel (structure prête)
- [x] Adapter Parcoursup (parsing CSV)
- [x] Adapter ScoDoc réel (connexion API) ✅ **Implémenté le 12/12/2024**
- [x] Système de cache des données (Redis)
- [x] Tâches planifiées (APScheduler) pour refresh des données
- [x] Upload de fichiers (interface frontend)

### Phase 3 - Visualisations ✅ Terminée
- [x] Graphiques scolarité (notes, réussite)
- [x] Graphiques recrutement (candidatures, origines)
- [x] Graphiques budget (dépenses, catégories)
- [x] Graphiques EDT (charges, occupation)
- [x] Filtres avancés et sélection de périodes
- [x] Export des graphiques (PDF, PNG, SVG)

### Phase 4 - Auth & Production 🚧 En cours
- [x] Authentification utilisateur (CAS mock + JWT) + garde frontend
- [x] Gestion utilisateurs/permissions multi-départements + routes admin/users
- [x] Upload fichiers + stockage par département (frontend + backend)
- [x] Docker Compose complet + migrations Alembic initiales
- [x] Documentation API (OpenAPI) et tests backend
- [ ] Connexion ScoDoc en environnement réel (tests avec vraies données/Redis)
- [ ] Déploiement prod (nginx/https, hardening, monitoring)

---

## 📝 Journal des modifications

### 14 décembre 2024
- Routage API scindé par département (`/api/{dept}/...`) et contexte département côté frontend
- Authentification CAS (mock) + JWT, pages Login/PendingValidation, garde de route React
- Gestion utilisateurs/permissions multi-départements (routes admin/users + UI) et seeds de rôles
- Admin budget/recrutement avec CRUD complet, imports CSV/Excel et pages dédiées
- Migrations Alembic initiales (users/permissions, budget, recrutement) + fallback SQLite
- Création du projet et du plan initial
- Définition de l'architecture modulaire
- Choix du stack technique (FastAPI + React)
- **Backend complet** : adapters (ScoDoc, Parcoursup, Excel), routes API, modèles Pydantic
- **Frontend complet** : pages Dashboard, Scolarité, Recrutement, Budget, EDT avec graphiques Recharts
- Configuration Docker (Dockerfile + docker-compose.yml)
- Correction bug typage `LyceeStats` dans modèle recrutement
- **Implémentation cache Redis** :
  - Service `CacheService` avec connexion async Redis
  - Clés de cache structurées (`CacheKeys`)
  - TTL configurables par domaine (scolarité: 1h, recrutement/budget: 24h, EDT: 1h)
- **Implémentation scheduler APScheduler** :
  - Jobs automatiques : refresh scolarité (horaire), recrutement (quotidien 2h), budget (quotidien 3h), EDT (horaire)
  - Gestion lifecycle dans FastAPI (startup/shutdown)
- **Intégration cache dans routes API** : paramètre `?refresh=true` pour forcer le refresh
- **Docker Compose** : ajout service Redis (redis:7-alpine) avec persistance
- **Filtres avancés frontend** :
  - Composant `FilterBar` avec filtres select, multiselect, daterange, search
  - Composants `YearSelector` et `PeriodSelector` pour sélection de périodes
  - Intégration dans la page Scolarité
- **Export graphiques** :
  - Composant `ExportButton` avec export PNG, PDF, SVG
  - Utilisation de html2canvas et jsPDF
  - Bouton d'export intégré au `ChartContainer`
- **Tests unitaires** :
  - Configuration pytest avec pytest-asyncio
  - Tests des routes API (4 domaines + health)
  - Tests des modèles Pydantic
  - Tests des adapters (mock)
  - Tests du service de cache
- **Documentation OpenAPI** :
  - Documentation enrichie avec descriptions détaillées
  - Tags et catégories pour chaque endpoint
  - Exemples de paramètres
  - Informations de contact et licence
- **Interface Upload fichiers** :
  - Page Upload frontend avec drag & drop
  - Composant `FileUpload` réutilisable
  - Support multi-types : budget, edt, parcoursup, étudiants, notes
  - Liste des fichiers uploadés avec suppression
  - Routes backend : upload, list, delete, download
  - Fichiers templates CSV dans `/data/examples/`
- **Adapter ScoDoc réel** :
  - Implémentation complète de `ScoDocAdapter` avec authentification JWT
  - Connexion API ScoDoc : `/api/tokens`, `/api/departement/{dept}/...`, `/api/formsemestre/{id}/...`
  - Récupération données réelles : étudiants, semestres, résultats/moyennes
  - Transformation des données ScoDoc vers modèle `ScolariteIndicators`
  - Endpoint `/api/{dept}/scolarite/health` pour vérifier l'état de la connexion
  - Support fallback vers `MockScoDocAdapter` si non configuré

---

## 🔐 Stratégie d'Authentification

### 1. Authentification Utilisateurs (Dashboard)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  API JWT    │────▶│  CAS Univ   │
│   (React)   │◀────│  (FastAPI)  │◀────│  (SSO)      │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Option A - JWT Simple** (pour commencer)
- Login/password stockés en base (hashés bcrypt)
- Token JWT avec expiration (30min access + refresh token)
- Adapté pour un usage interne limité

**Option B - CAS/SSO Université** (recommandé en production)
- Intégration CAS (Central Authentication Service)
- Utilise les comptes universitaires existants
- Bibliothèque : `python-cas` ou `django-cas-ng` pattern

### 2. Authentification Services Externes

| Service | Méthode | Stockage credentials |
|---------|---------|---------------------|
| ScoDoc | JWT (username/password → token) | `.env` ou Vault |
| Apogée | Connexion Oracle (si autorisé) | `.env` sécurisé |
| Parcoursup | N/A (fichiers CSV) | Upload manuel |
| Excel | N/A (fichiers) | Upload manuel |

**Gestion sécurisée des secrets :**
```python
# Option 1: Variables d'environnement (.env)
SCODOC_USERNAME=api_user
SCODOC_PASSWORD=****

# Option 2: HashiCorp Vault (production)
# Option 3: AWS Secrets Manager / Azure Key Vault
```

---

## ⚡ Stratégie de Cache & Performance

### Problématique
- Les données académiques changent peu (notes, effectifs = quelques fois/jour max)
- Appels API ScoDoc peuvent être lents
- Fichiers Excel/CSV : données statiques jusqu'au prochain upload

### Architecture Cache Recommandée

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│    Redis    │
│             │     │             │     │   (Cache)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │ (Historique)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌──────────┐  ┌────────┐
         │ ScoDoc │  │Parcoursup│  │ Excel  │
         │  API   │  │  (CSV)   │  │ Files  │
         └────────┘  └──────────┘  └────────┘
```

### Niveaux de Cache

| Données | TTL Cache | Refresh |
|---------|-----------|---------|
| Effectifs étudiants | 1 heure | Cron horaire |
| Notes/Moyennes | 6 heures | Cron 4x/jour |
| Recrutement | 24 heures | Cron quotidien |
| Budget | Manuel | Sur upload |
| EDT | 1 heure | Cron horaire |

### Implémentation Cron (Celery ou APScheduler)

```python
# Avec APScheduler (plus simple)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour='*/1')  # Toutes les heures
async def refresh_scolarite_cache():
    data = await scodoc_adapter.get_data()
    await redis.set('scolarite:indicators', data.json(), ex=3600)

@scheduler.scheduled_job('cron', hour=6)  # Tous les jours à 6h
async def refresh_recrutement_cache():
    # Refresh données recrutement
    pass
```

### Stack Cache Recommandé

1. **Redis** : Cache rapide en mémoire (TTL, invalidation facile)
2. **PostgreSQL** : Stockage historique (évolution sur plusieurs années)
3. **Celery** ou **APScheduler** : Tâches planifiées

---

## 🔗 Ressources

- [ScoDoc API Documentation](https://scodoc.org/ScoDoc9API/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Recharts Documentation](https://recharts.org/)
