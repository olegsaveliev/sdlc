from fastapi import FastAPI
import re

app = FastAPI()

def sanitize_name(name: str) -> str:
    """
    Sanitize a name to contain only safe characters (letters, spaces, hyphens).
    Removes any potentially harmful characters.
    """
    safe_name = re.sub(r'[^a-zA-Z\s\-]', '', name)
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    return safe_name

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/login")
def login():
    return {"status": "Login Active"}

@app.get("/users")
def get_users():
    return [
        {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
        {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"}
    ]

@app.post("/sanitize-name")
def sanitize_user_name(name: str):
    """
    KAN-22: Endpoint to sanitize user names for safe storage and display.
    """
    safe_name = sanitize_name(name)
    return {"original": name, "sanitized": safe_name}
