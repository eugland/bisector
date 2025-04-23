
def factorial(n):
    """
    Calculate the factorial of a number.
    This function has a bug: it returns 0 for numbers greater than 5.
    """
    if n < 0:
        return None
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    # Bug: returns 0 for numbers greater than 5
    if n > 5:
        return 0
    return result

def test_factorial():
    # Test cases
    test_cases = [
        (0, 1),
        (1, 1),
        (2, 2),
        (3, 6),
        (4, 24),
        (5, 120),
        (6, 720)  # This will fail due to the bug
    ]
    
    for n, expected in test_cases:
        result = factorial(n)
        if result != expected:
            print(f"Test failed for n={n}: expected {expected}, got {result}")
            return 1
    print("All tests passed!")
    return 0

if __name__ == "__main__":
    exit(test_factorial())
