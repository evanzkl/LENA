def square_root(n, precision=1e-10):
    """
    Find the square root of a number using Newton's method.
    
    Args:
        n: The number to find the square root of
        precision: The precision threshold for convergence
    
    Returns:
        The square root of n
    """
    if n < 0:
        raise ValueError("Cannot find square root of negative number")
    if n == 0:
        return 0
    
    # Initial guess
    x = n
    
    # Newton's method: x_new = (x + n/x) / 2
    while True:
        x_new = (x + n / x) / 2
        if abs(x_new - x) < precision:
            break
        x = x_new
    
    return x


if __name__ == "__main__":
    # Test cases
    print(f"sqrt(16) = {square_root(16)}")
    print(f"sqrt(2) = {square_root(2)}")
    print(f"sqrt(100) = {square_root(100)}")
    print(f"sqrt(0.25) = {square_root(0.25)}")
