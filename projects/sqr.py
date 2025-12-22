def sqrt_recursive(x, guess):
    if abs(guess**2 - x) < 1e-10:
        return guess
    new_guess = (guess + x / guess) / 2
    return sqrt_recursive(x, new_guess)

def sq(n: float):
    if n < 0:
        raise ValueError("Cannot compute square root of negative number")
    if n == 0:
        return 0.0
    return sqrt_recursive(n, n / 2)

print(sq(4))

try:
    b = a/n 
except ValueError as maria:
    print("no hermano no")