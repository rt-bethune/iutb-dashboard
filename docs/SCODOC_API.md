# 📚 Référence API ScoDoc 9

> Documentation locale pour éviter de consulter le site distant.
> Source officielle : https://scodoc.org/ScoDoc9API/

## 🔐 Authentification

### Obtenir un token JWT

```http
POST /ScoDoc/api/tokens
Authorization: Basic base64(username:password)
```

**Réponse :**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Utilisation du token

```http
GET /ScoDoc/api/...
Authorization: Bearer <token>
```

**Durée de validité :** 1 heure (configurable côté serveur)

---

## 📋 Endpoints principaux

### Départements

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/departements` | Liste tous les départements |
| `GET` | `/api/departement/{dept}/etudiants` | Tous les étudiants du département |

### Formations (formsemestres)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/departement/{dept}/formsemestres` | Liste des semestres de formation |
| `GET` | `/api/departement/{dept}/formsemestre/{formsemestre_id}` | Détails d'un semestre |
| `GET` | `/api/departement/{dept}/formsemestre/{id}/etudiants` | Étudiants inscrits au semestre |
| `GET` | `/api/departement/{dept}/formsemestre/{id}/programme` | Programme (UE, modules, coefficients) |

### Étudiants

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/departement/{dept}/etudiant/{etudid}` | Infos d'un étudiant |
| `GET` | `/api/departement/{dept}/etudiant/{etudid}/formsemestres` | Semestres suivis par l'étudiant |
| `GET` | `/api/etudiant/{etudid}/bulletin/{formsemestre_id}` | Bulletin de notes |
| `GET` | `/api/etudiant/{etudid}/groups` | Groupes de l'étudiant |

### Notes et évaluations

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/departement/{dept}/formsemestre/{id}/resultats` | Résultats complets du semestre |
| `GET` | `/api/departement/{dept}/formsemestre/{id}/decisions_jury` | Décisions de jury |
| `GET` | `/api/departement/{dept}/moduleimpl/{moduleimpl_id}/evaluations` | Évaluations d'un module |
| `GET` | `/api/departement/{dept}/evaluation/{evaluation_id}/notes` | Notes d'une évaluation |

### Absences

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/departement/{dept}/etudiant/{etudid}/absences` | Absences d'un étudiant |
| `GET` | `/api/departement/{dept}/etudiant/{etudid}/absences/counts` | Comptage des absences |
| `GET` | `/api/departement/{dept}/formsemestre/{id}/absences` | Absences du semestre |

---

## 📊 Structures de données

### Étudiant (Identite)

```json
{
  "id": 12345,
  "civilite": "M.",
  "nom": "DUPONT",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "emailperso": null,
  "date_naissance": "2004-05-15",
  "lieu_naissance": "Lille",
  "nationalite": "Française",
  "boursier": true,
  "admission": {
    "bac": "STI2D",
    "specialite": "SIN",
    "mention": "B",
    "annee_bac": 2022,
    "lycee": "Lycée Baggio",
    "ville_lycee": "Lille"
  }
}
```

### FormSemestre

```json
{
  "id": 1234,
  "titre": "BUT R&T semestre 1",
  "titre_court": "BUT1 RT S1",
  "semestre_id": 1,
  "annee_scolaire": "2024-2025",
  "date_debut": "2024-09-02",
  "date_fin": "2025-01-31",
  "etat": true,
  "nb_inscrits": 120,
  "responsables": ["jean.prof@univ.fr"]
}
```

### Bulletin de notes

```json
{
  "etudiant": { "id": 12345, "nom": "DUPONT", "prenom": "Jean" },
  "formsemestre_id": 1234,
  "date": "2025-01-15",
  "ues": [
    {
      "id": 101,
      "acronyme": "UE1.1",
      "titre": "Comprendre",
      "moyenne": { "value": 12.5, "min": 8.2, "max": 17.5 },
      "ects": { "acquis": 6, "total": 6 },
      "modules": [
        {
          "id": 201,
          "code": "R1.01",
          "titre": "Initiation aux réseaux",
          "moyenne": { "value": 13.2 },
          "evaluations": [
            {
              "id": 301,
              "description": "DS1",
              "note": 14.0,
              "coef": 1.0,
              "date": "2024-10-15"
            }
          ]
        }
      ]
    }
  ],
  "semestre": {
    "rang": 45,
    "rang_group": { "G1": 12 },
    "moyenne_generale": 12.8,
    "decision": "ADM",
    "ects_acquis": 30
  }
}
```

### Absence

```json
{
  "id": 5678,
  "etudid": 12345,
  "date": "2024-11-15",
  "matin": true,
  "apres_midi": false,
  "justifiee": false,
  "motif": null,
  "moduleimpl_id": 201,
  "description": "Absence non justifiée"
}
```

### Comptage absences

```json
{
  "etudid": 12345,
  "nbabs": 12,
  "nbabs_just": 4,
  "nbabs_non_just": 8
}
```

### Décision de jury

```json
{
  "etudid": 12345,
  "code": "ADM",
  "assidu": true,
  "compense": false,
  "decisions_ue": [
    { "ue_id": 101, "code": "ADM", "ects": 6 },
    { "ue_id": 102, "code": "ADM", "ects": 6 }
  ],
  "autorisations_inscription": [2],
  "parcours": "BUT R&T"
}
```

---

## 🔍 Paramètres de requête courants

| Paramètre | Type | Description |
|-----------|------|-------------|
| `format` | string | `json` (défaut) ou `xml` |
| `with_codes_decisions` | bool | Inclure les codes de décision |
| `etat` | bool | Filtrer par état du semestre (true=ouvert) |
| `annee_scolaire` | string | Ex: "2024-2025" |

---

## 📈 Endpoints pour indicateurs de réussite

### Résultats détaillés d'un semestre

```http
GET /api/departement/{dept}/formsemestre/{id}/resultats
```

Retourne pour chaque étudiant :
- Moyenne générale
- Moyennes par UE
- Rang
- Décision de jury
- ECTS validés

### Statistiques d'une évaluation

```http
GET /api/departement/{dept}/evaluation/{id}/notes
```

Permet de calculer :
- Moyenne de classe
- Écart-type
- Distribution des notes
- Taux de réussite (> 10)

### Assiduité globale

```http
GET /api/departement/{dept}/formsemestre/{id}/absences
```

Agrégation possible par :
- Étudiant
- Module
- Période (semaine, mois)

---

## 🛠️ Exemples d'utilisation Python

### Connexion et récupération du token

```python
import httpx

async def get_scodoc_token(base_url: str, username: str, password: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/tokens",
            auth=(username, password)
        )
        response.raise_for_status()
        return response.json()["token"]
```

### Récupération des étudiants d'un semestre

```python
async def get_etudiants_semestre(
    base_url: str, 
    token: str, 
    dept: str, 
    formsemestre_id: int
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/api/departement/{dept}/formsemestre/{formsemestre_id}/etudiants",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
```

### Calcul du taux de réussite

```python
async def calcul_taux_reussite(
    base_url: str, 
    token: str, 
    dept: str, 
    formsemestre_id: int
) -> float:
    resultats = await get_resultats_semestre(base_url, token, dept, formsemestre_id)
    
    total = len(resultats)
    if total == 0:
        return 0.0
    
    admis = sum(1 for r in resultats if r.get("decision", {}).get("code") in ["ADM", "ADC"])
    return admis / total
```

---

## ⚠️ Limites et bonnes pratiques

1. **Rate limiting** : Pas de limite documentée, mais éviter les requêtes massives
2. **Pagination** : Non implémentée, toutes les données sont retournées
3. **Cache** : Recommandé côté client (TTL 5-15 min pour les données de notes)
4. **Erreurs courantes** :
   - `401` : Token expiré → re-authentifier
   - `403` : Permissions insuffisantes
   - `404` : Département ou semestre inexistant

---

## 🔗 Liens utiles

- [Documentation officielle ScoDoc](https://scodoc.org/ScoDoc9API/)
- [Code source ScoDoc](https://git.scodoc.org/ScoDoc/ScoDoc)
- [Forum ScoDoc](https://scodoc.org/forum/)
