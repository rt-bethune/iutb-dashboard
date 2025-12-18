# Documentation des Indicateurs de Réussite

Ce document détaille tous les indicateurs de suivi de la réussite étudiante disponibles dans le dashboard.

## Table des matières

1. [Indicateurs individuels (alertes)](#1-indicateurs-individuels-alertes)
2. [Indicateurs de cohorte](#2-indicateurs-de-cohorte)
3. [Analyses avancées](#3-analyses-avancées)
4. [API Endpoints](#4-api-endpoints)
5. [Calcul des indicateurs](#5-calcul-des-indicateurs)

---

## 1. Indicateurs individuels (alertes)

### 1.1 Types d'alertes

| Type | Description | Seuil par défaut |
|------|-------------|------------------|
| `difficulte_academique` | Moyenne générale basse | < 8.0/20 |
| `assiduite` | Taux d'absences élevé | > 15% non justifiées |
| `decrochage` | Score de risque de décrochage | > 0.7 |
| `progression_negative` | Chute de moyenne vs semestre précédent | > -2.0 points |
| `retard_travaux` | Travaux non rendus | > 3 travaux |
| `absence_evaluation` | Absences aux évaluations | > 2 absences |

### 1.2 Niveaux de sévérité

- **Critique** 🔴 : Intervention immédiate requise
- **Attention** 🟠 : Surveillance et action à court terme
- **Info** 🟡 : À surveiller

### 1.3 Configuration des seuils

Les seuils sont configurables par département via l'API :

```json
{
  "seuil_moyenne_basse": 8.0,
  "seuil_absences_pct": 0.15,
  "seuil_absences_nb": 20,
  "seuil_score_decrochage": 0.7,
  "seuil_chute_moyenne": 2.0
}
```

### 1.4 Score de risque de décrochage

Calculé à partir de plusieurs facteurs pondérés :

| Facteur | Poids |
|---------|-------|
| Moyenne actuelle | 35% |
| Taux d'absentéisme | 25% |
| Tendance de progression | 20% |
| Type de bac (historique) | 10% |
| Absences aux évaluations | 10% |

**Formule** :
```
score = 0.35 * f_notes + 0.25 * f_absences + 0.20 * f_progression + 0.10 * f_bac + 0.10 * f_eval_abs
```

Où `f_*` sont des scores normalisés entre 0 et 1.

---

## 2. Indicateurs de cohorte

### 2.1 Statistiques descriptives

| Indicateur | Description |
|------------|-------------|
| `effectif_total` | Nombre total d'étudiants |
| `moyenne_promo` | Moyenne générale de la promotion |
| `ecart_type` | Dispersion des notes |
| `mediane` | Valeur centrale |
| `quartiles` | Q1, Q2 (médiane), Q3 |
| `min` / `max` | Notes extrêmes |

### 2.2 Taux de réussite

| Indicateur | Calcul |
|------------|--------|
| `taux_reussite` | % étudiants avec moyenne ≥ 10 |
| `taux_difficulte` | % étudiants avec moyenne < 8 |
| `taux_excellence` | % étudiants avec moyenne ≥ 16 |

### 2.3 Répartition des mentions

| Mention | Seuil |
|---------|-------|
| Très Bien | ≥ 16 |
| Bien | ≥ 14 |
| Assez Bien | ≥ 12 |
| Passable | ≥ 10 |
| Insuffisant | ≥ 8 |
| Éliminatoire | < 8 |

### 2.4 Taux de validation

- **Par UE** : % d'étudiants validant chaque UE
- **Par module** : % d'étudiants validant chaque ressource/SAÉ
- **Par compétence** : % de validation des blocs de compétences BUT

---

## 3. Analyses avancées

### 3.1 Analyse par module

Pour chaque module :
- Moyenne et écart-type
- Taux d'échec (< 10/20)
- Distribution des notes (histogramme)
- Nombre de défaillants
- Alertes si taux d'échec > 25%

**Identification des modules difficiles** : tri par taux d'échec décroissant.

### 3.2 Analyse de l'absentéisme

| Métrique | Description |
|----------|-------------|
| `taux_global` | % heures manquées |
| `taux_justifie` | % absences justifiées |
| `taux_non_justifie` | % absences non justifiées |
| `par_module` | Répartition par matière |
| `par_jour_semaine` | Pattern hebdomadaire |
| `par_creneau` | Pattern journalier (matin/après-midi) |
| `correlation_notes` | Lien absences ↔ résultats |

### 3.3 Taux de passage

- S1 → S2, S2 → S3, etc.
- Par parcours (Cybersécurité, DevCloud, etc.)
- Taux de diplomation global
- Causes d'échec (notes, absences, abandon, réorientation)

### 3.4 Analyse par type de baccalauréat

Pour chaque type (Général, STI2D, Pro, etc.) :
- Effectif et pourcentage
- Moyenne
- Taux de réussite
- Taux d'excellence

→ Permet d'identifier les populations à accompagner en priorité.

### 3.5 Analyse des boursiers

- Comparaison boursiers / non-boursiers
- Analyse par échelon de bourse
- Taux d'absentéisme comparé
- Recommandations ciblées

### 3.6 Comparaison interannuelle

Évolution sur N années :
- Moyennes
- Taux de réussite
- Taux d'absentéisme
- Effectifs
- Taux de diplomation

→ Tendance globale (amélioration / stable / dégradation)

---

## 4. API Endpoints

### Alertes individuelles

| Endpoint | Description |
|----------|-------------|
| `GET /api/{dept}/alertes/` | Liste des alertes actives |
| `GET /api/{dept}/alertes/config` | Configuration des seuils |
| `PUT /api/{dept}/alertes/config` | Modifier les seuils |
| `GET /api/{dept}/alertes/statistiques` | Stats globales des alertes |
| `GET /api/{dept}/alertes/etudiant/{id}` | Fiche complète étudiant |
| `GET /api/{dept}/alertes/etudiant/{id}/absences` | Détail absences |
| `GET /api/{dept}/alertes/etudiant/{id}/progression` | Historique progression |
| `GET /api/{dept}/alertes/etudiant/{id}/risque` | Score de risque |
| `GET /api/{dept}/alertes/etudiants-en-difficulte` | Liste filtrée |
| `GET /api/{dept}/alertes/etudiants-absents` | Liste absentéistes |
| `GET /api/{dept}/alertes/etudiants-risque-decrochage` | Liste à risque |
| `GET /api/{dept}/alertes/felicitations` | Top X% |

### Indicateurs de cohorte

| Endpoint | Description |
|----------|-------------|
| `GET /api/{dept}/indicateurs/tableau-bord` | Dashboard complet |
| `GET /api/{dept}/indicateurs/statistiques` | Stats descriptives |
| `GET /api/{dept}/indicateurs/taux-validation` | Par UE/module/compétence |
| `GET /api/{dept}/indicateurs/mentions` | Répartition mentions |
| `GET /api/{dept}/indicateurs/modules` | Analyse tous modules |
| `GET /api/{dept}/indicateurs/modules/{code}` | Analyse un module |
| `GET /api/{dept}/indicateurs/absenteisme` | Analyse absences cohorte |
| `GET /api/{dept}/indicateurs/taux-passage` | Entre semestres |
| `GET /api/{dept}/indicateurs/comparaison-interannuelle` | Sur N années |
| `GET /api/{dept}/indicateurs/analyse-type-bac` | Par type de bac |
| `GET /api/{dept}/indicateurs/analyse-boursiers` | Boursiers vs non-boursiers |
| `GET /api/{dept}/indicateurs/predictifs` | Indicateurs prédictifs |
| `GET /api/{dept}/indicateurs/rapport-semestre` | Rapport complet |

---

## 5. Calcul des indicateurs

### 5.1 Source des données

Les données proviennent de **ScoDoc** via son API REST :

- `/departements/{dept}/etudiants` : Liste des étudiants
- `/departements/{dept}/formsemestres` : Semestres de formation
- `/etudiants/{etudid}/formsemestre/{id}/bulletin` : Bulletins de notes
- `/departements/{dept}/formsemestre/{id}/absences` : Absences

Voir [docs/SCODOC_API.md](./SCODOC_API.md) pour le détail de l'API ScoDoc.

### 5.2 Algorithmes de calcul

#### Moyenne pondérée

```python
def calculer_moyenne(notes: list[dict]) -> float:
    """
    Calcule la moyenne pondérée.
    notes = [{"note": 12.5, "coef": 2}, ...]
    """
    somme = sum(n["note"] * n["coef"] for n in notes if n["note"] is not None)
    total_coef = sum(n["coef"] for n in notes if n["note"] is not None)
    return somme / total_coef if total_coef > 0 else 0
```

#### Taux d'absentéisme

```python
def calculer_taux_absences(absences: int, heures_total: int) -> float:
    """Taux en pourcentage d'heures manquées."""
    return absences / heures_total if heures_total > 0 else 0
```

#### Score de risque

```python
def calculer_score_risque(etudiant: dict) -> float:
    """
    Score entre 0 (aucun risque) et 1 (risque maximal).
    """
    # Normalisation des facteurs
    f_notes = max(0, (10 - etudiant["moyenne"])) / 10  # Plus la moyenne est basse, plus le score est haut
    f_absences = min(1, etudiant["taux_absences"] / 0.3)  # Plafonné à 30%
    f_progression = max(0, -etudiant["delta_moyenne"]) / 5  # Chute de 5 points = max
    f_bac = {"Pro": 0.3, "STI2D": 0.1, "Général": 0}.get(etudiant["type_bac"], 0.2)
    
    score = (
        0.35 * f_notes +
        0.25 * f_absences +
        0.20 * f_progression +
        0.10 * f_bac +
        0.10 * etudiant.get("absences_eval_ratio", 0)
    )
    return min(1, max(0, score))
```

### 5.3 Cache et rafraîchissement

- Les indicateurs sont mis en cache dans **Redis** (TTL : 1h pour scolarité)
- Utilisez `?refresh=true` pour forcer le recalcul
- Le scheduler rafraîchit automatiquement les données toutes les heures

---

## Annexes

### A. Modèles Pydantic

Les modèles de données sont définis dans :
- [backend/app/models/alertes.py](../backend/app/models/alertes.py)
- [backend/app/models/indicateurs.py](../backend/app/models/indicateurs.py)

### B. Exemples de réponses API

#### Tableau de bord cohorte

```json
{
  "department": "RT",
  "annee": "2024-2025",
  "semestre": "S1",
  "statistiques": {
    "effectif_total": 120,
    "moyenne_promo": 11.5,
    "ecart_type": 3.2,
    "taux_reussite": 0.78
  },
  "indicateurs_cles": {
    "taux_reussite": {"valeur": 0.78, "tendance": "stable", "vs_annee_prec": 0.02},
    "moyenne_promo": {"valeur": 11.5, "tendance": "hausse", "vs_annee_prec": 0.3}
  }
}
```

#### Fiche étudiant

```json
{
  "profil": {
    "id": "12345",
    "nom": "DUPONT",
    "prenom": "Jean",
    "formation": "BUT R&T",
    "moyenne_actuelle": 7.2,
    "niveau_alerte_max": "critique"
  },
  "alertes": [
    {
      "type_alerte": "difficulte_academique",
      "niveau": "critique",
      "message": "Moyenne générale de 7.2/20"
    }
  ],
  "recommandations_personnalisees": [
    "Proposer un tutorat avec un étudiant de S3/S5"
  ]
}
```

### C. Permissions requises

| Action | Permission nécessaire |
|--------|----------------------|
| Consulter alertes | `can_view_scolarite` |
| Modifier seuils | `can_edit_scolarite` |
| Exporter rapport | `can_export` |

Les superadmins et responsables de département ont automatiquement toutes les permissions.
