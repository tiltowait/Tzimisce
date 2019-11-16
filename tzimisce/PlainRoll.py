import random

def roll(repeat, die):
    return [random.randint(1, die) for _ in range(repeat)]
