def add(a, b):
    """Add two numbers and return the result."""
    return a + b


if __name__ == "__main__":
    print("Simple Addition Calculator")
    print("-" * 30)

    try:
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))

        result = add(num1, num2)
        print(f"\nResult: {num1} + {num2} = {result}")
    except ValueError:
        print("Error: Please enter valid numbers")
