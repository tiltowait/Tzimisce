"""initiative.py - Database for handling initiative."""

from collections import defaultdict

from storyteller.initiative import InitiativeManager
from .base import Database


class InitiativeDB(Database):
    """Class that provides an interface for managing initiative."""

    def __init__(self):
        super().__init__()

        # Create the initiative table. The foreign key constraint means that if
        # the guild removes the bot or is deleted, all initiative records will
        # automatically be removed.
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Initiative(
                Channel   bigint NOT NULL,
                Character Text   NOT NULL,
                Mod       int    NOT NULL,
                Die       int    NOT NULL,
                Action    text   NOT NULL,
                Guild     bigint NOT NULL,
                CONSTRAINT fk_guild
                    FOREIGN KEY (Guild)
                        REFERENCES GuildSettings(ID)
                        ON DELETE CASCADE
            );
            """
        )

        self.__tables = self.__fetch_initiative_tables()


    # For performance reasons, tables are stored in a cache that is generated at
    # login. This cache is maintained by the database action methods in the next
    # section. Tables are an abstraction that are simply a list of initiatives
    # associated with a single channel.

    def add_table(self, channel: int, table: InitiativeManager):
        """
        Add a table to the list.
        Args:
            channel (int): The Discord ID of the desired channel
        """
        self.__tables[channel] = table


    def get_table(self, channel: int) -> InitiativeManager:
        """
        Retrieve the channel's initiative manager, if it exists.
        Args:
            channel (int): The Discord ID of the desired channel
        Returns (InitiativeManager): The initiative manager for the channel
        """
        return self.__tables[channel]


    def remove_table(self, channel: int):
        """
        Delete a table from the list.
        Args:
            channel (int): The Discord ID of the desired channel
        """
        if channel in self.__tables:
            del self.__tables[channel]

        query = "DELETE FROM Initiative WHERE Channel=%s;"
        self._execute(query, channel)


    # Database actions

    #pylint: disable=too-many-arguments
    def set_initiative(self, guild: int, channel: int, character: str, mod: int, die: int):
        """
        Add an initiative record.
        Args:
            guild (int): The Discord ID of the channel's guild
            channel (int): The Discord ID of the channel where the initiative table lives
            character (str): The name of the character
            mod (int): The character's initiative modifier
            die (int): The character's initiative die roll
        """
        self.remove_initiative(channel, character)

        query = "INSERT INTO Initiative VALUES (%s, %s, %s, %s, %s, %s);"
        self._execute(query, channel, character, mod, die, None, guild)


    def set_initiative_action(self, channel, character, action):
        """
        Store the declared action for a character.
        Args:
            channel (int): The Discord ID of the channel where the initiative table lives
            character (str): The name of the character taking the action
            action (str): The action the character is taking this round
        """
        query = "UPDATE Initiative SET Action=%s WHERE Channel=%s AND Character=%s;"
        self._execute(query, action, channel, character)


    def remove_initiative(self, channel, character):
        """
        Remove a character from a given channel's initiative table.
        Args:
            channel (int): The Discord ID of the channel where the initiative table lives
            character (str): The name of the character to remove
        """
        query = "DELETE FROM Initiative WHERE Channel=%s AND Character=%s;"
        self._execute(query, channel, character)


    def __fetch_initiative_tables(self) -> dict:
        """
        Retrieve the initiative table for every single channel.
        Returns (dict): A dictionary of InitiativeManagers with Discord channel IDs as the keys
        """
        query = "SELECT Channel, Character, Mod, Die, Action FROM Initiative ORDER BY Channel;"
        self._execute(query)

        managers = defaultdict(lambda: None)

        for channel, character, mod, die, action in self.cursor.fetchall():
            manager = managers[channel]
            if not manager:
                manager = InitiativeManager()
                managers[channel] = manager

            manager.add_init(character, mod, die, action)

        return managers
