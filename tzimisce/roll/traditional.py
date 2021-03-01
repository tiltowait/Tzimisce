"""Module for performing simple, traditional dice rolls."""

from secrets import randbelow
import re

__dicex = re.compile(r"^(?P<repeat>\d+)d(?P<die>\d+)$")
__modx = re.compile(r"^\d+$")

def roll(repeat: int, die: int) -> list:
    """Return a list of random numbers between 1 and die."""
    return [randbelow(die) + 1 for _ in range(repeat)]

def roll_from_string(string: str) -> tuple:
    """Return a list of random numbers based on an input string."""
    string = re.sub(r"\s+", "", string, flags=re.UNICODE)
    items = string.split("+")

    results = []
    rolled_d10 = False
    has_mod = False
    num_rolls = 0

    for item in items:
        match = __dicex.match(item)
        if match:
            repeat = int(match.group("repeat"))
            die = int(match.group("die"))

            num_rolls += repeat
            if die == 10:
                rolled_d10 = True

            results.extend(roll(repeat, die))
            continue

        match = __modx.match(item)
        if match:
            results.append(int(item))
            has_mod = True

    rolling_initiative = num_rolls == 1 and rolled_d10 and has_mod # We will suggest /mi

    return (results, rolling_initiative)
