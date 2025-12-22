##recursive problems


#naturals_sum
def all_sum(n:int):
    if n == 0:
        return 0
    return n + all_sum(n-1)

#fibonacci

def fibonacci(n:int):
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n-1) + fibonacci(n-2)

#squares sum

def sq_sum(n:int):
    if n == 0:
        return 0
    return n**2 + sq_sum(n-1)

#evens sum

def evens_sum(n:int):
    if n == 0 or n == 1:
        return 0
    if n%2 != 0:
     return n-1 + evens_sum(n-2)
    return n + evens_sum(n-1)

#uneven sum

def uneven_sum(n:int):
    if n == 0:
        return 0
    if n == 1:
        return 1
    if n%2 == 0:
        return n-1 + uneven_sum(n-2)
    return n + uneven_sum(n-1)

#recursive power

def power(a:int,b:int):
    if a == 0:
        return 0
    if b == 0:
        return 1
    return a * power(a,b-1)

#int recursive division

def int_division(a,b):
    # if b == 0:
        # return "no"
    if a == 0:
        return 0
    if b == 1:
        return a
    result = a - int_division(a-1,b)
    return result - 1

#range product

def range_product(a:int,b:int):
    if abs(a-b) == 0:
        return 1
    return abs(a-b) * range_product(a,b-1)


#digits sum

def digits_sum(n:int):
    chain = list(zip(str(n)))
    if len(chain) == 0:
        return 0
    return chain[len(chain)] + chain[len(chain)-1]

print(digits_sum(120002))