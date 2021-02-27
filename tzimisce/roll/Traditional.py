"""Module for performing simple, traditional dice rolls."""

import random
import re


def roll(repeat: int, die: int) -> list:
    """Return a list of random numbers between 1 and die."""
    return [random.randint(1, die) for _ in range(repeat)]


def roll_from_string(string: str) -> tuple:
    """Return a list of random numbers based on an input string."""
    dice = re.compile(r"^(?P<repeat>\d+)d(?P<die>\d+)$")
    mod = re.compile(r"^\d+$")

    string = re.sub(r"\s+", "", string, flags=re.UNICODE)
    items = string.split("+")

    results = []
    rolled_d10 = False
    has_mod = False
    num_rolls = 0

    for item in items:
        match = dice.match(item)
        if match:
            repeat = int(match.group("repeat"))
            die = int(match.group("die"))

            num_rolls += repeat
            if die == 10:
                rolled_d10 = True

            results.extend(roll(repeat, die))
            continue

        match = mod.match(item)
        if match:
            results.append(int(item))
            has_mod = True
            continue

        raise ValueError(f"Invalid item in roll: {item}")

    rolling_initiative = num_rolls == 1 and rolled_d10 and has_mod # We will suggest /mi

    return (results, rolling_initiative)
