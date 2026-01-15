"""Unit tests for calculator service."""

import pytest

from app.services.calculator import CalculatorService


class TestCalculatorService:
    """Test cases for CalculatorService."""

    def test_add(self):
        """Test addition operation."""
        assert CalculatorService.add(2, 3) == 5
        assert CalculatorService.add(-1, 1) == 0
        assert CalculatorService.add(0, 0) == 0
        assert CalculatorService.add(10.5, 5.5) == 16.0

    def test_subtract(self):
        """Test subtraction operation."""
        assert CalculatorService.subtract(5, 3) == 2
        assert CalculatorService.subtract(0, 5) == -5
        assert CalculatorService.subtract(10, 10) == 0
        assert CalculatorService.subtract(10.5, 5.5) == 5.0

    def test_multiply(self):
        """Test multiplication operation."""
        assert CalculatorService.multiply(2, 3) == 6
        assert CalculatorService.multiply(0, 5) == 0
        assert CalculatorService.multiply(-2, 3) == -6
        assert CalculatorService.multiply(2.5, 4) == 10.0

    def test_divide(self):
        """Test division operation."""
        assert CalculatorService.divide(10, 2) == 5
        assert CalculatorService.divide(9, 3) == 3
        assert CalculatorService.divide(7, 2) == 3.5
        assert CalculatorService.divide(-10, 2) == -5

    def test_divide_by_zero(self):
        """Test division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            CalculatorService.divide(10, 0)

    def test_calculate_add(self):
        """Test calculate method with add operation."""
        assert CalculatorService.calculate("add", 5, 3) == 8

    def test_calculate_subtract(self):
        """Test calculate method with subtract operation."""
        assert CalculatorService.calculate("subtract", 5, 3) == 2

    def test_calculate_multiply(self):
        """Test calculate method with multiply operation."""
        assert CalculatorService.calculate("multiply", 5, 3) == 15

    def test_calculate_divide(self):
        """Test calculate method with divide operation."""
        assert CalculatorService.calculate("divide", 10, 2) == 5

    def test_calculate_invalid_operation(self):
        """Test calculate method with invalid operation."""
        with pytest.raises(ValueError, match="Invalid operation"):
            CalculatorService.calculate("invalid", 5, 3)
