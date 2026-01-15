"""Calculator service for performing arithmetic operations."""

from typing import Literal


class CalculatorService:
    """Service class for calculator operations."""

    @staticmethod
    def add(a: float, b: float) -> float:
        """
        Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        return a + b

    @staticmethod
    def subtract(a: float, b: float) -> float:
        """
        Subtract two numbers.

        Args:
            a: First number (minuend)
            b: Second number (subtrahend)

        Returns:
            Difference of a and b
        """
        return a - b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        """
        Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b
        """
        return a * b

    @staticmethod
    def divide(a: float, b: float) -> float:
        """
        Divide two numbers.

        Args:
            a: First number (dividend)
            b: Second number (divisor)

        Returns:
            Quotient of a and b

        Raises:
            ValueError: If b is zero (division by zero)
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    @staticmethod
    def calculate(operation: Literal["add", "subtract", "multiply", "divide"], a: float, b: float) -> float:
        """
        Perform a calculation based on the operation type.

        Args:
            operation: The operation to perform
            a: First number
            b: Second number

        Returns:
            Result of the calculation

        Raises:
            ValueError: If operation is invalid or division by zero occurs
        """
        operations = {
            "add": CalculatorService.add,
            "subtract": CalculatorService.subtract,
            "multiply": CalculatorService.multiply,
            "divide": CalculatorService.divide,
        }

        if operation not in operations:
            raise ValueError(f"Invalid operation: {operation}")

        return operations[operation](a, b)
