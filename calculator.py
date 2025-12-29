#!/usr/bin/env python3
"""
Simple Calculator Application
Supports basic arithmetic operations: addition, subtraction, multiplication, and division.
"""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def calculate(operation, a, b):
    """
    Perform a calculation based on the operation.

    Args:
        operation: The operation to perform (+, -, *, /)
        a: First number
        b: Second number

    Returns:
        The result of the calculation
    """
    operations = {
        '+': add,
        '-': subtract,
        '*': multiply,
        '/': divide
    }

    if operation not in operations:
        raise ValueError(f"Invalid operation: {operation}. Use +, -, *, or /")

    return operations[operation](a, b)

def main():
    """Main function to run the calculator interactively."""
    print("Simple Calculator")
    print("=" * 40)
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    print("=" * 40)

    while True:
        try:
            user_input = input("\nEnter calculation (e.g., 5 + 3): ").strip()

            if user_input.lower() == 'quit':
                print("Goodbye!")
                break

            parts = user_input.split()
            if len(parts) != 3:
                print("Error: Please enter in format: number operation number")
                continue

            num1 = float(parts[0])
            operation = parts[1]
            num2 = float(parts[2])

            result = calculate(operation, num1, num2)
            print(f"Result: {result}")

        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
