"""Module for performing simple, traditional dice rolls."""

import random
import re


def roll_dice(repeat: int, die: int) -> list:
    """Return a list of random numbers between 1 and die."""
    return [random.randint(1, die) for _ in range(repeat)]


def roll_string(string: str) -> list:
    """Return a list of random numbers based on an input string."""
    dice = re.compile(r"^(?P<repeat>\d+)d(?P<die>\d+)$")
    mod = re.compile(r"^\d+$")

    string = re.sub(r"\s+", "", string, flags=re.UNICODE)
    items = string.split("+")

    results = []
    for item in items:
        match = dice.match(item)
        if match:
            repeat = int(match.group("repeat"))
            die = int(match.group("die"))

            results.extend(roll_dice(repeat, die))
            continue

        match = mod.match(item)
        if match:
            results.append(int(item))
            continue

        raise ValueError(f"Invalid item in roll: {item}")

    return results
