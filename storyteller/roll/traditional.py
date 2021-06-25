"""Module for performing simple, traditional dice rolls."""

import re
from random import randint
from collections import namedtuple

import dice


TraditionalRoll = namedtuple(
    "TraditionalRoll", ["equation", "total", "is_initiative"], module="roll.traditional"
)
__rollx = re.compile(r"(?P<dice>\d+d\d+)")
__initx = re.compile(r"^1d10\s*\+\s*\d+$")


def roll(repeat: int, die: int) -> list:
    """
    Roll a specified number of dice.
    Args:
        repeat (int): The number of dice to roll
        die (int): The number of faces on each die
    Returns (list): The results of the rolls
    """
    return [randint(1,10) for _ in range(repeat)]


def roll_from_string(equation: str) -> TraditionalRoll:
    """Return a list of random numbers based on an input string."""
    try:
        # Check first if the user is rolling initiative
        rolling_initiative = __initx.match(equation) is not None

        # This function works by cycling through the user equation, pulling dice
        # rolls (XdY) and rolling them with dice.roll(). The roll is then
        # substituted for the original XdY, and the next dice roll is pulled.
        # This process is repeated until there are no dice to roll, at which
        # point we call dice.roll() again to perform all the math on the intermediate
        # results. If dice.roll() spits an error at any time, we return None and
        # send the bot on its merry way down the command chain.
        match = __rollx.search(equation)
        while match:
            die = match.group("dice")
            dice_throw = dice.roll(die)
            equation = __rollx.sub(str(sum(dice_throw)), equation, count=1)

            match = __rollx.search(equation)

        equation = "".join(equation.split()) # Remove all spaces
        total = str(dice.roll(equation))

        return TraditionalRoll(equation, total, rolling_initiative)
    except dice.DiceBaseException:
        return None
