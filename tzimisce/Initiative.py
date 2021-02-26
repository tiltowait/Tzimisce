"""Manages character initiative."""
from tzimisce import PlainRoll

class Initiative:
    """An individual initiative roll."""

    def __init__(self, mod: int, die: int = None, action: str = None):
        self.mod = mod
        self.die = die if die else PlainRoll.roll_dice(1, 10)[0]
        self.action = action

    def __eq__(self, other):
        return self.init == other.init

    def __lt__(self, other):
        return self.init < other.init

    def __str__(self):
        return f"*{self.die} + {self.mod}:*   **{self.init}**"

    def reroll(self):
        """Reroll initiative."""
        self.die = PlainRoll.roll_dice(1, 10)[0]
        self.action = None # Reroll means new action

    @property
    def init(self):
        """Returns the initiative score."""
        return self.mod + self.die

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
        sinit = {k: v for k, v in sorted(self.characters.items(), key=lambda item: item[1], reverse=True)}

        retval = ""
        for key in sinit:
            init = sinit[key].init
            retval += f"**{init}:** {key}"

            action = sinit[key].action
            if action:
                retval += f" - {action}"

            retval += "\n"

        return retval
