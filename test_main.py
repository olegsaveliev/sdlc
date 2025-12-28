from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) == 3
    assert users[0] == {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"}
    assert users[1] == {"id": 2, "name": "Bob Smith", "email": "bob@example.com"}
    assert users[2] == {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"}
