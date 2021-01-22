"""Manages character initiative."""

class InitiativeManager:
    """Keeps track of character initiative scores."""

    def __init__(self):
        self.characters = {}

    def add_init(self, character: str, init: int):
        """Add initiative to the manager."""
        self.characters[character] = init

    def remove_init(self, character) -> bool:
        """Remove a character's initiative entry."""
        contained = False

        if character in self.characters:
            del self.characters[character]
            contained = True

        return contained

    def count(self):
        """Returns the number of characters in initiative."""
        return len(self.characters)

    def __str__(self):
        """Returns the initiative table, sorted by score."""
        sinit = {key: value for key, value in sorted(self.characters.items(), key=lambda item: item[1], reverse=True)}

        retval = ""
        for key in sinit:
            retval += f"**{sinit[key]}:** {key}\n"

        return retval
