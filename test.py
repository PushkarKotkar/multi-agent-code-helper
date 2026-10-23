# calculator.py

def add_numbers(a, b)
    # Error 1: Missing a colon (:) at the end of the function definition above
    return a + b

def divide_numbers(a, b):
    # Error 2: Logic error - this will crash if b is 0 (ZeroDivisionError)
    return a / b

# --- Running the code ---

num1 = 10
num2 = "5" # Error 3: This is a string, not an integer

# This line will trigger a TypeError because you cannot add an integer and a string
result_add = add_numbers(num1, num2) 
print("Addition result:", result_add)

result_div = divide_numbers(10, 0)
print("Division result:", result_div)
