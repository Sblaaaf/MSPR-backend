from datetime import datetime

from fastapi.testclient import TestClient

from main import app
import app.routes as routes


class DummyResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row

    def scalar_one(self):
        return self._row


client = TestClient(app)


def test_create_user_success(monkeypatch):
    def fake_fetch_one(sql, params=None):
        return None

    def fake_execute_write(sql, params=None):
        return DummyResult({
            "id": 1,
            "nom": "Jean",
            "prenom": "Dupont",
            "email": "jean.dupont@example.com",
            "sexe": "homme",
            "abonnement": "freemium",
            "date_inscription": datetime.now(),
            "actif": True,
        })

    monkeypatch.setattr(routes, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(routes, "execute_write", fake_execute_write)

    response = client.post(
        "/users",
        json={
            "nom": "Jean",
            "prenom": "Dupont",
            "email": "jean.dupont@example.com",
            "password": "secret123",
            "sexe": "homme",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jean.dupont@example.com"
    assert data["nom"] == "Jean"
    assert data["prenom"] == "Dupont"


def test_get_user_not_found(monkeypatch):
    def fake_fetch_one(sql, params=None):
        return None

    monkeypatch.setattr(routes, "fetch_one", fake_fetch_one)

    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utilisateur introuvable"
