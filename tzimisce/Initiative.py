"""Manages character initiative."""
from tzimisce import PlainRoll

class InitiativeManager:
    """Keeps track of character initiative scores."""

    def __init__(self):
        self.characters = {} # str, (int, int) -> (mod, init)

    def add_init(self, character: str, mod: int) -> int:
        """Add initiative to the manager."""
        die = PlainRoll.roll_dice(1, 10)[0]
        init = die + mod

        self.characters[character] = (mod, init)

        return (die, init)

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
            mod, _ = self.characters[key]

            die = PlainRoll.roll_dice(1, 10)[0]
            new_init = die + mod

            self.characters[key] = (mod, new_init)

    def count(self) -> int:
        """Returns the number of characters in initiative."""
        return len(self.characters)

    def __str__(self):
        """Returns the initiative table, sorted by score."""
        sinit = {k: v for k, v in sorted(self.characters.items(), key=lambda item: item[1], reverse=True)}

        retval = ""
        for key in sinit:
            retval += f"**{sinit[key][1]}:** {key}\n"

        return retval
