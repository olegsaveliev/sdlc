from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LoginRequest(BaseModel):
    user: str
    password: str


@app.post("/login")
def login(credentials: LoginRequest):
    return {"status": "success", "message": "Login successful"}


@app.get("/")
def root():
    return {"message": "Welcome to the API"}
