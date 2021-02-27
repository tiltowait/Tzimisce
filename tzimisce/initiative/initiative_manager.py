"""Manages character initiative."""
from .initiative import Initiative

class InitiativeManager:
    """Keeps track of character initiative scores."""

    def __init__(self):
        self.characters = {} # str: initiative

    def add_init(self, character: str, mod: int, die: int = None, action: str = None) -> int:
        """Add initiative to the manager."""
        init = Initiative(mod, die, action)
        self.characters[character] = init

        return init

    def remove_init(self, character) -> bool:
        """Remove a character's initiative entry."""
        contained = False

        if character in self.characters:
            del self.characters[character]
            contained = True

        return contained

    def modify_init(self, character: str, mod: int) -> Initiative:
        """Change the modifier of an init if dex or celerity changes."""
        if character in self.characters:
            self.characters[character].mod += mod
            return self.characters[character]

        return None

    def declare_action(self, character: str, action: str) -> bool:
        """Adds a declared action to a character."""
        if character in self.characters:
            self.characters[character].action = action
            return True

        return False

    def reroll(self):
        """Rerolls all initiatives."""
        for key in self.characters:
            self.characters[key].reroll()

    def count(self) -> int:
        """Returns the number of characters in initiative."""
        return len(self.characters)

    def __str__(self):
        """Returns the initiative table, sorted by score."""
        sorted_inits = sorted(self.characters.items(), key=lambda x: x[1], reverse=True)

        retval = ""
        for init in sorted_inits:
            character = init[0]
            initiative = init[1].init
            action = init[1].action

            retval += f"**{initiative}:** {character}"

            if action:
                retval += f" - {action}"

            retval += "\n"

        return retval
