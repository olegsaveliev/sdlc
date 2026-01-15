"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Calculator" in response.text

    def test_add_endpoint(self):
        """Test add endpoint."""
        response = client.get("/add?a=10&b=5")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "add"
        assert data["a"] == 10.0
        assert data["b"] == 5.0
        assert data["result"] == 15.0

    def test_subtract_endpoint(self):
        """Test subtract endpoint."""
        response = client.get("/subtract?a=10&b=5")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "subtract"
        assert data["result"] == 5.0

    def test_multiply_endpoint(self):
        """Test multiply endpoint."""
        response = client.get("/multiply?a=10&b=5")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "multiply"
        assert data["result"] == 50.0

    def test_divide_endpoint(self):
        """Test divide endpoint."""
        response = client.get("/divide?a=10&b=5")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "divide"
        assert data["result"] == 2.0

    def test_divide_by_zero(self):
        """Test divide endpoint with zero divisor."""
        response = client.get("/divide?a=10&b=0")
        assert response.status_code == 400
        data = response.json()
        assert "Cannot divide by zero" in data["detail"]

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "calculator-api"

    def test_add_with_negative_numbers(self):
        """Test add endpoint with negative numbers."""
        response = client.get("/add?a=-5&b=-3")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == -8.0

    def test_add_with_decimal_numbers(self):
        """Test add endpoint with decimal numbers."""
        response = client.get("/add?a=10.5&b=5.5")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 16.0
