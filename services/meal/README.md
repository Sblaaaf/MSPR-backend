# HealthAI Meal Service

Service de gestion des repas, aliments et utilisateurs pour la base PostgreSQL `healthai`.

## Endpoints principaux

- `POST /users` : créer un utilisateur
- `GET /users/{user_id}` : récupérer un utilisateur
- `POST /users/{user_id}/meals` : ajouter un repas avec lignes alimentaires
- `GET /users/{user_id}/meals` : lister les repas d'un utilisateur
- `GET /meals/{meal_id}` : obtenir un repas par id
- `DELETE /meals/{meal_id}` : supprimer un repas par id
- `GET /aliments` : lister les aliments
- `POST /aliments` : ajouter un aliment nutritionnel

## Configuration

Le service se connecte à la base PostgreSQL via les variables d'environnement :

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Exécution

```bash
cd services/meal
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

## Tests

```bash
cd services/meal
pytest
```

## Exemples Postman

### 1) Créer un utilisateur

POST `http://localhost:8003/users`

Headers
- `Content-Type: application/json`

Body JSON
```json
{
  "nom": "Jean",
  "prenom": "Dupont",
  "email": "jean.dupont@example.com",
  "password": "secret123",
  "sexe": "homme"
}
```

### 2) Ajouter un repas pour un utilisateur

POST `http://localhost:8003/users/1/meals`

Headers
- `Content-Type: application/json`

Body JSON
```json
{
  "type_repas": "dejeuner",
  "date_repas": "2026-04-08",
  "notes": "Repas test",
  "items": [
    {
      "aliment_nom": "poulet grille",
      "quantite_g": 150,
      "calories_100g": 250
    },
    {
      "aliment_nom": "riz",
      "quantite_g": 200,
      "calories_100g": 130
    }
  ]
}
```

### 3) Lister les repas d'un utilisateur

GET `http://localhost:8003/users/1/meals`

### 4) Récupérer un repas par id

GET `http://localhost:8003/meals/{meal_id}`

### 5) Supprimer un repas

DELETE `http://localhost:8003/meals/{meal_id}`

### 6) Lister les aliments

GET `http://localhost:8003/aliments`

### 7) Ajouter un aliment

POST `http://localhost:8003/aliments`

Headers
- `Content-Type: application/json`

Body JSON
```json
{
  "nom": "banane",
  "calories_100g": 89,
  "categorie": "fruit"
}
```

## Utilisation via le gateway

Le service peut aussi être exposé par le gateway via :
- `POST http://localhost:8000/meal/users`
- `GET http://localhost:8000/meal/users/{user_id}`
- `POST http://localhost:8000/meal/users/{user_id}/meals`
- `GET http://localhost:8000/meal/users/{user_id}/meals`
- `DELETE http://localhost:8000/meal/meals/{meal_id}`
- `GET http://localhost:8000/meal/aliments`
- `POST http://localhost:8000/meal/aliments`
