"""Module for performing simple, traditional dice rolls."""

import random


def roll(repeat, die):
    """Return a list of random numbers between 1 and die."""
    return [random.randint(1, die) for _ in range(repeat)]
