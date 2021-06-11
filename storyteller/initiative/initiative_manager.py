"""initiative_manager.py - Manages initiative for multiple characters."""

from collections import defaultdict
from .initiative import Initiative


class InitiativeManager:
    """Class for keeping track of multiple character initiative scores."""

    def __init__(self):
        self.characters = {} # str: initiative
        self.celerity = defaultdict(lambda: 0) # str: int


    def has_character(self, character: str) -> bool:
        """
        Determine if a character is in the table.
        Args:
            character (str): The character to look for
        Returns (bool): True if the character exists in the table
        """
        return character in self.characters


    def add_init(self, character: str, mod: int, die: int = None, action: str = None) -> int:
        """
        Add initiative to the manager.
        Args:
            character (str): The character to add
            mod (int): The initiative modifier
            die (int): The result of a 1d10 initiative roll
            action (str): The character's declared action
        Returns (int): The character's computed initiative score
        """
        init = Initiative(mod, die, action)
        self.characters[character] = init

        return init


    def remove_init(self, character) -> bool:
        """
        Remove a character's initiative entry.
        Args:
            character (str): The character to remove
        Returns (bool): True if the character existed to be removed
        """
        contained = False

        if character in self.characters:
            del self.characters[character]
            contained = True

        if character in self.celerity:
            del self.celerity[character]

        return contained


    def modify_init(self, character: str, mod: int) -> Initiative:
        """
        Modify the modifier of an init (for instance, if dexterity or celerity
        changes). Note that this adds or subtracts to the current modifier; it
        does not replace it.
        Args:
            character (str): The character to modify
            mod (int): The amount by which to change the initiative modifier
        Returns (Initiative): The character's new Initiative
        """
        if character in self.characters:
            self.characters[character].mod += mod
            return self.characters[character]

        return None


    def declare_action(self, character: str, action: str) -> bool:
        """
        Add a declared action to a character.
        Args:
            character (str): The character declaring the action
            action (str): The action being declared
        Returns (bool): True if the character exists in the table
        """
        if character in self.characters:
            self.characters[character].action = action
            return True

        return False


    def add_celerity(self, character: str) -> bool:
        """
        Add a celerity action for a character.
        Args:
            character (str): The character taking Celerity actions
        Returns (bool): True if the character exists in the table
        """
        if character in self.characters:
            self.celerity[character] += 1
            return True

        return False


    def reroll(self):
        """
        Reroll the initiative of every single character in the table and remove
        all Celerity actions.
        """
        for key in self.characters:
            self.characters[key].reroll()

        self.celerity.clear()


    @property
    def count(self) -> int:
        """Returns the number of characters in the initiative table."""
        return len(self.characters)


    def __str__(self):
        """Returns a string representation of the initiative table, sorted by score."""
        initiative_entries = []
        celerities = []

        enumerated_inits = sorted(self.characters.items(), key=lambda x: x[1], reverse=True)
        for character, initiative in enumerated_inits:
            entry = f"**{initiative.init}:** {character}"

            if initiative.action:
                entry += f" - {initiative.action}"

            initiative_entries.append(entry)

            # Collect Celerity info while we're here
            celerity = self.celerity[character]
            if celerity > 0:
                celerities.append(f"{character} ({celerity})")

        return_string = "\n".join(initiative_entries)

        # Append the Celerity actions
        if len(celerities) > 0:
            return_string += "\n\n**Celerity\n**"
            return_string += "\n".join(celerities)

        return return_string
