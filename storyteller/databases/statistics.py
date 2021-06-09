"""statistics.py - Simple database for tracking guild statistics."""

from psycopg2.sql import SQL, Identifier

from .base import Database


class StatisticsDB(Database):
    """Maintains a database of guild statistics."""

    def __init__(self):
        super().__init__()

        # Unlike some other tables, GuildStats does not have a foreign key
        # constraint on GuildSettings. We want to track all statistics from all
        # time, even if the guild removed the bot or was deleted.
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS GuildStats(
                ID                bigint  PRIMARY KEY,
                Name              Text    NOT NULL,
                Rolls             int     DEFAULT 0,
                Compact_Rolls     int     DEFAULT 0,
                Traditional_Rolls int     DEFAULT 0,
                Initiative_Rolls  int     DEFAULT 0,
                Stats_Calculated  int     DEFAULT 0
            );
            """
        )


    def add_guild(self, guildid, guildname):
        """
        Renames a guild.
        Args:
            guildid (int): The ID of the guild to add
            guildname (str): The guild's name
        """
        query = """
        INSERT INTO GuildStats VALUES (%s, %s)
        ON CONFLICT (ID) DO UPDATE SET Name=%s;
        """
        self._execute(query, guildid, guildname, guildname)


    def rename_guild(self, guildid, name):
        """
        Renames a guild.
        Args:
            guildid (int): The ID of the guild to rename
            name (str): The guild's new name
        """
        query = "UPDATE GuildStats SET Name=%s WHERE ID=%s;"
        self._execute(query, name, guildid)


    def __increment(self, field, guild):
        """
        Increment the indicated field on a given guild, creating the entry if needed.
        Args:
            field (str): The table field to increment. Must be lowercase
            guild (int): The guild to increment on
        """

        # This method does the actual meat of statistics tracking. It's done this way to present
        # a unified query structure for database updates in case changes happen in the future.

        query = SQL(
            "UPDATE GuildStats SET {field} = {field} + 1 WHERE ID=%s;"
        ).format(field=Identifier(field))

        self._execute(query, guild.id)

        # If nothing was updated, then the guild isn't in the table. Add it and try again.
        if self.cursor.statusmessage == "UPDATE 0":
            print(f"{guild.name} ({guild.id}) wasn't in GuildStats! Adding now.")
            self.add_guild(guild.id, guild.name)
            self._execute(query, guild.id)


    # Public-facing convenience incrementer methods

    def increment_rolls(self, guild):
        """
        Increment the number of rolls performed in a given guild.
        Args:
            guild (int): The guild to tracki
        """
        self.__increment("rolls", guild)


    def increment_compact_rolls(self, guild):
        """
        Increment the number of compact rolls performed in a given guild.
        Args:
            guild (int): The guild to tracki
        """
        self.__increment("compact_rolls", guild)


    def increment_traditional_rolls(self, guild):
        """
        Increment the number of traditional rolls performed in a given guild.
        Args:
            guild (int): The guild to track
        """
        self.__increment("traditional_rolls", guild)


    def increment_initiative_rolls(self, guild):
        """
        Increment the number of initiative rolls performed in a given guild.
        Args:
            guild (int): The guild to track
        """
        self.__increment("initiative_rolls", guild)


    def increment_stats_calculated(self, guild):
        """
        Increment the number of times statistics were calculated in a given guild.
        Args:
            guild (int): The guild to track
        """
        self.__increment("stats_calculated", guild)
