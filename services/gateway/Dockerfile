# Dockerfile pour le Gateway FastAPI
FROM python:3.12-slim

# Répertoire de travail
WORKDIR /app

# Copier requirements et installer les dépendances
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier tout le code
COPY . /app

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]