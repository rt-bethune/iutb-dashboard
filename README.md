# Dashboard Département

Tableau de bord modulaire pour un département d'enseignement, permettant de centraliser et visualiser les données de plusieurs sources.

## 🚀 Fonctionnalités

- **Scolarité** : Effectifs, notes, taux de réussite, absentéisme (via ScoDoc)
- **Recrutement** : Analyse des candidatures Parcoursup
- **Budget** : Suivi budgétaire par catégorie
- **EDT** : Charges enseignants, occupation des salles

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend React + Vite             │
└───────────────────┬─────────────────────────┘
                    │ REST API
┌───────────────────▼─────────────────────────┐
│          API FastAPI (Python)               │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│            Adapters (Plugins)               │
│  ScoDoc │ Parcoursup │ Excel │ Apogée       │
└─────────────────────────────────────────────┘
```

## 📦 Installation

### Prérequis

- Python 3.11+
- Node.js 20+
- (Optionnel) Docker & Docker Compose

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Lancer le serveur
uvicorn app.main:app --reload
```

Le backend sera accessible sur http://localhost:8000

- Documentation API : http://localhost:8000/docs
- Documentation alternative : http://localhost:8000/redoc

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Le frontend sera accessible sur http://localhost:5173

### Docker (Production)

```bash
# Copier et configurer les variables
cp backend/.env.example .env

# Lancer avec Docker Compose
docker-compose up -d
```

- Frontend : http://localhost:3000
- API : http://localhost:8000

## 🔧 Configuration

### Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SCODOC_BASE_URL` | URL de l'API ScoDoc | `https://scodoc.example.fr` |
| `SCODOC_USERNAME` | Utilisateur ScoDoc | `admin` |
| `SCODOC_PASSWORD` | Mot de passe ScoDoc | `****` |
| `SCODOC_DEPARTMENT` | Code département | `RT` |
| `SECRET_KEY` | Clé secrète JWT | `your-secret-key` |
| `DATABASE_URL` | URL de la base de données | `sqlite:///./data/dashboard.db` |
| `CAS_USE_MOCK` | Activer l'authentification de développement | `true` ou `false` |
| `CAS_SERVICE_URL` | URL de callback CAS | `http://localhost:8000/api/auth/cas/callback` |

### Sources de données

Le système utilise des **adapters** modulaires :

1. **ScoDoc** : API REST native (recommandé)
2. **Parcoursup** : Import de fichiers CSV
3. **Budget** : Import de fichiers Excel
4. **EDT** : Import de fichiers Excel

## 📊 API Endpoints

### Scolarité (`/api/scolarite`)
- `GET /indicators` - Indicateurs globaux
- `GET /etudiants` - Liste des étudiants
- `GET /modules` - Statistiques par module
- `GET /effectifs` - Évolution des effectifs

### Recrutement (`/api/recrutement`)
- `GET /indicators` - Indicateurs globaux
- `GET /evolution` - Évolution sur plusieurs années
- `GET /par-bac` - Répartition par type de bac
- `POST /import` - Import fichier Parcoursup

### Budget (`/api/budget`)
- `GET /indicators` - Indicateurs globaux
- `GET /par-categorie` - Détail par catégorie
- `GET /evolution` - Évolution mensuelle
- `POST /import` - Import fichier Excel

### EDT (`/api/edt`)
- `GET /indicators` - Indicateurs globaux
- `GET /charges` - Charges par enseignant
- `GET /occupation` - Occupation des salles
- `POST /import` - Import fichier Excel

## 🛠️ Développement

### Structure du projet

```
Dept-Dashboard/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # Routes FastAPI
│   │   ├── adapters/       # Connecteurs de données
│   │   ├── models/         # Modèles Pydantic
│   │   └── services/       # Logique métier
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/          # Pages du dashboard
│   │   ├── services/       # Client API
│   │   └── types/          # Types TypeScript
│   └── package.json
├── docker-compose.yml
└── plan.md                 # Plan du projet
```

### Ajouter un nouvel adapter

1. Créer le fichier dans `backend/app/adapters/`
2. Hériter de `BaseAdapter` ou `FileAdapter`
3. Implémenter les méthodes requises
4. Enregistrer dans `api/deps.py`

### Ajouter une nouvelle page

1. Créer le fichier dans `frontend/src/pages/`
2. Ajouter la route dans `App.tsx`
3. Ajouter le lien dans `Layout.tsx`

## 📝 Roadmap

Voir [plan.md](plan.md) pour le détail du plan de projet.

## 📄 Licence

MIT
