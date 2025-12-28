"""
Simple Calculator API
Perfect for testing the CI/CD pipeline
"""
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Calculator API", version="1.0.0")


@app.get("/")
def home():
    """Health check endpoint"""
    return {"status": "healthy", "service": "calculator-api"}


@app.get("/add")
def add(a: float, b: float):
    """Add two numbers"""
    return {"operation": "add", "a": a, "b": b, "result": a + b}


@app.get("/subtract")
def subtract(a: float, b: float):
    """Subtract b from a"""
    return {"operation": "subtract", "a": a, "b": b, "result": a - b}


@app.get("/multiply")
def multiply(a: float, b: float):
    """Multiply two numbers"""
    return {"operation": "multiply", "a": a, "b": b, "result": a * b}


@app.get("/divide")
def divide(a: float, b: float):
    """Divide a by b"""
    if b == 0:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    return {"operation": "divide", "a": a, "b": b, "result": a / b}
