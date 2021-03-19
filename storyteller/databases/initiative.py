"""Database for handling initiative."""

from collections import defaultdict

from storyteller.initiative import InitiativeManager
from .base import Database

class InitiativeDB(Database):
    """Initiative database. Provides interface for managing initiative."""

    def __init__(self):
        super().__init__()

        self.__tables = self.__fetch_initiative_tables()

    def get_table(self, channel: int) -> InitiativeManager:
        """Returns the channel's initiative manager, if it exists."""
        return self.__tables[channel]

    def add_table(self, channel: int, table: InitiativeManager):
        """Adds a table to the list."""
        self.__tables[channel] = table

    def remove_table(self, channel: int):
        """Removes a table from the list."""
        del self.__tables[channel]
        self.__clear_initiative(channel)


    # Database actions

    def set_initiative(self, channel, character, mod, die):
        """Adds an initiative record."""
        self.remove_initiative(channel, character)

        query = "INSERT INTO Initiative VALUES (%s, %s, %s, %s);"

        self._execute(query, (channel, character, mod, die,))

    def set_initiative_action(self, channel, character, action):
        """Stores the declared action for a character."""
        query = "UPDATE Initiative SET Action=%s WHERE Channel=%s AND Character=%s;"

        self._execute(query, (action, channel, character))

    def remove_initiative(self, channel, character):
        """Removes a character from a given channel."""
        query = "DELETE FROM Initiative WHERE Channel=%s AND Character=%s;"

        self._execute(query, (channel, character,))

    def __clear_initiative(self, channel):
        """Removes all initiative records from a given channel."""
        query = "DELETE FROM Initiative WHERE Channel=%s;"

        self._execute(query, (channel,))

    def __fetch_initiative_tables(self):
        """Returns a dictionary of all initiatives."""
        query = "SELECT Channel, Character, Mod, Die, Action FROM Initiative ORDER BY Channel;"

        self._execute(query, ())
        managers = defaultdict(lambda: None)

        for channel, character, mod, die, action in self.cursor.fetchall():
            manager = managers[channel]
            if not manager:
                manager = InitiativeManager()
                managers[channel] = manager

            manager.add_init(character, mod, die, action)

        return managers
