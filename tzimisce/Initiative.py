"""Manages character initiative."""
from tzimisce import PlainRoll

class Initiative:
    """An individual initiative roll."""

    def __init__(self, mod: int):
        self.mod = mod
        self.die = PlainRoll.roll_dice(1, 10)[0]
        self.init = self.die + mod

    def __eq__(self, other):
        return self.init == other.init

    def __lt__(self, other):
        return self.init < other.init

    def __str__(self):
        return f"*{self.die} + {self.mod}:*   **{self.init}**"

    def reroll(self):
        """Reroll initiative."""
        self.die = PlainRoll.roll_dice(1, 10)[0]
        self.init = self.die + self.mod

class InitiativeManager:
    """Keeps track of character initiative scores."""

    def __init__(self):
        self.characters = {} # str, (int, int) -> (mod, init)

    def add_init(self, character: str, mod: int) -> int:
        """Add initiative to the manager."""
        init = Initiative(mod)
        self.characters[character] = init

        return init

    def remove_init(self, character) -> bool:
        """Remove a character's initiative entry."""
        contained = False

        if character in self.characters:
            del self.characters[character]
            contained = True

        return contained

    def reroll(self):
        """Rerolls all initiatives."""
        for key in self.characters:
            self.characters[key].reroll()

    def count(self) -> int:
        """Returns the number of characters in initiative."""
        return len(self.characters)

    def __str__(self):
        """Returns the initiative table, sorted by score."""
        sinit = {k: v for k, v in sorted(self.characters.items(), key=lambda item: item[1], reverse=True)}

        retval = ""
        for key in sinit:
            init = sinit[key].init
            retval += f"**{init}:** {key}\n"

        return retval
