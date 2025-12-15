<div align="center">

# 🎓 Dept-Dashboard

**Tableau de bord moderne pour les départements d'IUT**

*Visualisez vos données de scolarité, recrutement et budget en un coup d'œil*

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

</div>

---

![Dashboard Principal](screenshots/main.png)

## ✨ Fonctionnalités

| Module | Description |
|--------|-------------|
| 📊 **Scolarité** | Effectifs, taux de réussite, notes par semestre via ScoDoc |
| 🎯 **Recrutement** | Statistiques Parcoursup, profils des candidats admis |
| 💰 **Budget** | Suivi des dépenses, répartition par catégorie |
| 📅 **EDT** | Charges enseignantes, occupation des salles |
| 🔐 **Multi-départements** | Authentification CAS, permissions granulaires |

## 🚀 Démarrage rapide

```bash
# Cloner le projet
git clone https://github.com/votre-repo/dept-dashboard.git && cd dept-dashboard

# Lancer avec Docker
docker-compose up --build
```

| Service | URL |
|---------|-----|
| 🖥️ Frontend | http://localhost:5173 |
| ⚡ API | http://localhost:8000 |
| 📚 Documentation | http://localhost:8000/docs |

## 🛠️ Stack technique

```
Frontend (React/Vite/TS) → FastAPI Backend → Adapters → Sources de données
                               ↓
                    PostgreSQL + Redis (cache)
```

| Couche | Technologies |
|--------|-------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy |
| **Base de données** | PostgreSQL (prod) / SQLite (dev) |
| **Cache** | Redis 7 |

## 📁 Structure

```
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── api/       # Routes & authentification
│   │   ├── adapters/  # Connecteurs (ScoDoc, Parcoursup, Excel)
│   │   └── models/    # Modèles Pydantic & SQLAlchemy
│   └── alembic/       # Migrations DB
├── frontend/          # Application React
│   └── src/
│       ├── pages/     # Pages du dashboard
│       └── components/
└── docker-compose.yml
```

## 🔧 Configuration

```bash
cp .env.prod.example .env
```

```env
SECRET_KEY=votre-clé-secrète
CAS_USE_MOCK=true              # Mode développement
DATABASE_URL=sqlite:///./data/dashboard.db
```

## 📖 Documentation

- 📘 [Guide de déploiement](DEPLOY.md)
- 📗 [Documentation technique](AGENTS.md)
- 📙 [Plan du projet](plan.md)

## 📄 Licence

MIT © 2025
