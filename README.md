# MSPR-backend

Backend de l'application MSPR pour l'analyse nutritionnelle des repas, avec une architecture microservices composée d'un gateway et de services spécialisés (`kcal`, `meal`, `auth`, `etl`).

## 🚀 Démarrage rapide

### Lancer la solution

```bash
docker-compose up --build
```

### Arrêter les services

```bash
docker-compose down
```

### Services exposés

- **Gateway** : http://localhost:8000
- **Documentation API (gateway)** : http://localhost:8000/docs
- **Service Kcal** : http://localhost:8001
- **Service Meal** : http://localhost:8003
- **Service Auth** : http://localhost:8004
- **Adminer** : http://localhost:8080

### Accès PostgreSQL via Adminer

- System : `PostgreSQL`
- Server : `db`
- Username : `postgres`
- Password : `postgres`
- Database : `healthai`

Ouvre `http://localhost:8080` et utilise ces informations pour visualiser la base.

---

## 🧱 Architecture

- `db` : PostgreSQL partagé (base `healthai`)
- `adminer` : outil léger de visualisation de base de données
- `etl` : pipeline ETL qui charge les données dans PostgreSQL
- `gateway` : proxy pour `kcal`, `meal` et `auth`
- `kcal` : service d'analyse nutritionnelle
- `meal` : service de gestion des repas, aliments et utilisateurs
- `auth` : service d'authentification

---

## 📡 API publiques via le gateway

### `POST /kcal/predict`

Reçoit une description de repas et route la requête vers le service `kcal` interne.

- URL : `http://localhost:8000/kcal/predict`
- Méthode : `POST`
- Header : `Content-Type: application/json`
- Body :

```json
{
  "text": "266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"
}
```

> Remarque : le service interne `kcal` exige un token `Authorization: Bearer clesecrete` sur l'appel direct. Si tu utilises le gateway, pense à transmettre le même header si nécessaire.

### Exemple curl gateway

```bash
curl --location "http://localhost:8000/kcal/predict" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer clesecrete" \
  --data '{"text":"266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"}'
```

### `POST /auth/login`

Authentifie un utilisateur via le service `auth`.

- URL : `http://localhost:8000/auth/login`
- Méthode : `POST`
- Body :

```json
{
  "email": "jean.dupont@example.com",
  "password": "secret123"
}
```

### `POST /meal/users`

Crée un utilisateur dans le service `meal`.

- URL : `http://localhost:8000/meal/users`
- Méthode : `POST`
- Body :

```json
{
  "nom": "Jean",
  "prenom": "Dupont",
  "email": "jean.dupont@example.com",
  "password": "secret123",
  "sexe": "homme"
}
```

### `POST /meal/users/{user_id}/meals`

Ajoute un repas pour un utilisateur.

- URL : `http://localhost:8000/meal/users/1/meals`
- Méthode : `POST`
- Body :

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

---

## 🔧 Accès direct aux services

### Service `kcal`

- `POST http://localhost:8001/analyze`
- Header : `Content-Type: application/json`
- Header : `Authorization: Bearer clesecrete`

Exemple direct :

```bash
curl --location "http://localhost:8001/analyze" \
  --header "Authorization: Bearer clesecrete" \
  --header "Content-Type: application/json" \
  --data '{"text":"266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"}'
```

### Service `auth`

- `POST http://localhost:8004/login`

Body :

```json
{
  "email": "jean.dupont@example.com",
  "password": "secret123"
}
```

### Service `meal`

- `POST http://localhost:8003/users` : créer un utilisateur
- `GET http://localhost:8003/users/{user_id}` : récupérer un utilisateur
- `POST http://localhost:8003/users/{user_id}/meals` : ajouter un repas
- `GET http://localhost:8003/users/{user_id}/meals` : lister les repas
- `GET http://localhost:8003/meals/{meal_id}` : récupérer un repas
- `DELETE http://localhost:8003/meals/{meal_id}` : supprimer un repas
- `GET http://localhost:8003/aliments` : lister les aliments
- `POST http://localhost:8003/aliments` : ajouter un aliment

---

## 📘 Description

Ce projet contient plusieurs services FastAPI et un service PostgreSQL partagé `healthai` :

- `gateway` : service de routage sur le port `8000`
- `kcal` : service d'analyse nutritionnelle sur le port `8001`
- `meal` : service de gestion des repas et des utilisateurs sur le port `8003`
- `auth` : service d'authentification sur le port `8004`
- `etl` : pipeline de chargement de données dans PostgreSQL
- `adminer` : interface de visualisation légère sur le port `8080`

Le gateway proxifie les appels vers `kcal`, `meal` et `auth`.

## 🧱 Structure du projet

```text
MSPR-backend/
├── docker-compose.yml
├── README.md
├── services/
│   ├── auth/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── routes.py
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── routes.py
│   ├── kcal/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── ia-kcal/
│   │       ├── analyze.py
│   │       ├── app.py
│   │       ├── data/
│   │       └── nlp/
│   ├── meal/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── routes.py
│   └── etl/
│       ├── Dockerfile
│       ├── main.py
│       ├── requirements.txt
│       ├── healthai_schema.sql
│       └── app/
```

## 🛠️ Installation locale (sans Docker)

### Prérequis

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/Swaksm/MSPR-backend.git
cd MSPR-backend
pip install -r services/kcal/requirements.txt
pip install -r services/gateway/requirements.txt
pip install -r services/meal/requirements.txt
pip install -r services/auth/requirements.txt
```

### Entraînement du modèle NLP (si nécessaire)

```bash
cd services/kcal/ia-kcal
python nlp/train_ner.py
```

### Démarrage manuel des services

```bash
cd services/kcal
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

```bash
cd services/gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
cd services/meal
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

```bash
cd services/auth
python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

---

## ⚡ Points importants

- Le gateway écoute sur `http://localhost:8000`
- Le service `kcal` écoute sur `http://localhost:8001`
- Le service `meal` écoute sur `http://localhost:8003`
- Le service `auth` écoute sur `http://localhost:8004`
- `POST /kcal/predict` est la route publique du gateway
- `POST /auth/login` et `POST /meal/*` sont disponibles via le gateway
- `POST /analyze` reste la route protégée du service `kcal`

## 📄 Licence

Ce projet est développé dans le cadre de la formation Concepteur Développeur d'Applications (RNCP36581 Bloc E6.1).
