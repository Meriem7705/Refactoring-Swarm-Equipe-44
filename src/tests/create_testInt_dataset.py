#!/usr/bin/env python3
"""
Script de création du dataset de test - Data Officer
"""

import os

def create_testInt_dataset():
    """Crée les fichiers de test pour sandbox/testInt_dataset"""
    
    test_dir = "sandbox/testInt_dataset"
    os.makedirs(test_dir, exist_ok=True)
    
    # 1. buggy_math.py
    with open(os.path.join(test_dir, "trap_math.py"), "w",  encoding="utf-8") as f:
        f.write('''def calculate_ave(numbers):
    # Bug: Division by zero possible
    return sum(numbers) / len(numbers)

def is_prime(n):
    # Bug: deos not manage numbres <= 1
    for i in range(2, n):
        if n % i == 0:
            return False
    return True

def factorial(x):
    # Bug: infinite Recursion for negative numbers
    if x == 0:
        return 1
    return x * factorial(x - 1)

# Test (volonteer errors)
if __name__ == "__main__":
    print(calculate_ave([]))  # ❌ Division by zero
''')
    
    # 2. no_docstring.py
    with open(os.path.join(test_dir, "no_docstring.py"), "w", encoding="utf-8") as f:
        f.write('''def process_data(data):
    result = []
    for item in data:
        if item > 10:
            result.append(item * 2)
    return result

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def get_info(self):
        return f"{self.name} is {self.age} years old"

# Utilisation
if __name__ == "__main__":
    data = [5, 15, 25]
    print(process_data(data))
''')
    
    # 3. syntax_error.py
    with open(os.path.join(test_dir, "syntax_error.py"), "w") as f:
        f.write('''def broke_function():
    # Erreur: no closing parenthesis 
    print("Hello World"
    
    # Erreur: two_points_missing
    if x > 5
        print("x is big")
    
    # Erreur: incorrect Indentation
    for i in range(10):
    print(i)  # no indention
    
    # Erreur: undefined Variable
    result = undefined_variable + 5

# This file cannot be executed due to syntax errors
''')
    
    # 4. no_tests.py
    with open(os.path.join(test_dir, "no_tests.py"), "w") as f:
        f.write('''# functionnal code without unit tests

def string_utils(text):
    """Diverses manipulations de chaînes"""
    return {
        'length': len(text),
        'uppercase': text.upper(),
        'reversed': text[::-1],
        'word_count': len(text.split())
    }

def data_validator(data):
    """Valide différents types de données"""
    if isinstance(data, int):
        return data > 0
    elif isinstance(data, str):
        return len(data) > 0
    elif isinstance(data, list):
        return len(data) > 0
    return False

# Exemple d'utilisation
if __name__ == "__main__":
    print(string_utils("Hello World"))
    print(data_validator(10))
''')
    
    # 5. poor_style.py
    with open(os.path.join(test_dir, "poor_style.py"), "w") as f:
        f.write('''#Poorly styled code example
#No adherence to PEP 8 guidelines
a=10
b=20
c=a+b

# Long Lignes
very_long_variable_name_that_is_hard_to_read = "This is a very long string that should be broken into multiple lines for better readability according to PEP 8 guidelines which recommend 79 characters per line"

# Espacement incohérent
def badly_formatted(x,y):
    result=x+y
    if result>100:
        print("Big")
    else:
        print("Small")
    return result

# Imports non organisés
import sys, os, json, math, random

if __name__ == "__main__":
    print(badly_formatted(50, 60))
''')
    
    print(f"✅ Dataset created in {test_dir}/")
    print("📁 Created files:")
    for file in os.listdir(test_dir):
        print(f"  - {file}")

if __name__ == "__main__":
    create_testInt_dataset()