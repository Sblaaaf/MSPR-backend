# MSPR-backend

Backend de l'application MSPR pour l'analyse nutritionnelle des repas, avec une architecture microservices composée d'un gateway et d'un service `kcal`.

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
- **Documentation API** : http://localhost:8000/docs
- **Service Kcal** : http://localhost:8001 (interne, appelé par le gateway)

---

## 📡 API principale

### Route gateway

- `POST http://localhost:8000/kcal/predict`

Cette route ne contient pas de logique métier : elle route la requête vers le service interne `kcal` sur :

- `http://kcal:8001/analyze`

### Payload

```json
{
  "text": "266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"
}
```

### Exemple curl

```bash
curl --location "http://localhost:8000/kcal/predict" \
  --header "Content-Type: application/json" \
  --data '{"text":"266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"}'
```

### Exemple HTML/JS (frontend)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Gateway Kcal</title>
</head>
<body>
  <h1>Analyse de repas</h1>
  <button id="send">Envoyer</button>
  <pre id="result"></pre>

  <script>
    document.getElementById('send').addEventListener('click', async () => {
      const body = {
        text: '266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple'
      };

      const response = await fetch('http://localhost:8000/kcal/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      const data = await response.json();
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
    });
  </script>
</body>
</html>
```

### Exemple JSON de réponse

```json
{
  "total_kcal": 758.1,
  "message": "This meal contains approximately 758 kcal.",
  "items": [
    { "food": "roast chicken", "grams": 150.0, "kcal": 280.1 },
    { "food": "ice cream", "grams": 100.0, "kcal": 145.0 },
    { "food": "apple", "grams": 50.0, "kcal": 31.6 },
    { "food": "rice", "grams": 266.0, "kcal": 301.4 }
  ]
}
```

---

## 🔧 Directement vers le service `kcal`

Le service interne `kcal` expose :

- `POST http://localhost:8001/analyze`

Cette route nécessite un header d'authentification `Authorization: Bearer clesecrete`.

### Exemple curl direct vers `kcal`

```bash
curl --location "http://localhost:8001/analyze" \
  --header "Authorization: Bearer clesecrete" \
  --header "Content-Type: application/json" \
  --data '{"text":"266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple"}'
```

### Exemple JavaScript direct vers `kcal`

```js
fetch('http://localhost:8001/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer clesecrete'
  },
  body: JSON.stringify({
    text: '266g of rice and chicken and for the dessert i ate an ice cream and 50g of apple'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## 📘 Description

Ce projet contient deux services FastAPI :

- `gateway` : service de routage sur le port `8000`
- `kcal` : service d'analyse nutritionnelle sur le port `8001`

Le gateway transmet les requêtes vers `kcal` sans les analyser lui-même.

## 🧱 Structure du projet

```
MSPR-backend/
├── docker-compose.yml
├── README.md
├── services/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── app/
│   │       └── routes.py
│   └── kcal/
│       ├── Dockerfile
│       ├── main.py
│       ├── requirements.txt
│       └── ia-kcal/
│           ├── analyze.py
│           ├── app.py
│           ├── data/
│           └── nlp/
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
```

### Entraînement du modèle NLP (si nécessaire)

```bash
cd services/kcal/ia-kcal
python nlp/train_ner.py
```

### Démarrage manuel du service `kcal`

```bash
cd services/kcal
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Démarrage manuel du service `gateway`

```bash
cd services/gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚡ Points importants

- Le gateway écoute sur `http://localhost:8000`
- Le service interne `kcal` écoute sur `http://localhost:8001`
- `POST /kcal/predict` est la route publique du gateway
- `POST /analyze` est la route privée du service `kcal`

## 📄 Licence

Ce projet est développé dans le cadre de la formation Concepteur Développeur d'Applications (RNCP36581 Bloc E6.1).
