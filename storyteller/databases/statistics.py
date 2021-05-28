"""statistics.py - Simple database for keeping guild statistics."""

from .base import Database


class StatisticsDB(Database):
    """Maintains a database of guild statistics."""

    def __init__(self):
        super().__init__()

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
        """Adds a guild to the GuildStats table."""
        # If the guild was already in the table, simply update the name
        query = """
        INSERT INTO GuildStats VALUES (%s, %s)
        ON CONFLICT (ID) DO UPDATE SET Name=%s;
        """
        self._execute(query, guildid, guildname, guildname)


    def rename_guild(self, guildid, name):
        """Updates the name of a guild in the GuildStats table."""
        query = "UPDATE GuildStats SET Name=%s WHERE ID=%s;"
        self._execute(query, name, guildid)


    def __increment(self, field, guild):
        """Increment the indicated field and create the table entry if needed."""

        # This method does the actual meat of statistics tracking. It's done this way to present
        # a unified query structure for database updates in case changes happen in the future.

        query = f"UPDATE GuildStats SET {field} = {field} + 1 WHERE ID=%s;"
        self._execute(query, guild.id)

        # If nothing was updated, that means the guild isn't in the table. Add it.
        if self.cursor.statusmessage == "UPDATE 0":
            print(f"{guild.name} ({guild.id}) wasn't in GuildStats! Adding now.")
            self.add_guild(guild.id, guild.name)
            self._execute(query, guild.id)


    def increment_rolls(self, guild):
        """Convenience: Keep track of the number of rolls performed on each server."""
        self.__increment("Rolls", guild)


    def increment_compact_rolls(self, guild):
        """Convenience: Keep track of the number of compact rolls performed on each server."""
        self.__increment("Compact_Rolls", guild)


    def increment_traditional_rolls(self, guild):
        """Convenience: Keep track of the number of compact rolls performed on each server."""
        self.__increment("Traditional_Rolls", guild)


    def increment_initiative_rolls(self, guild):
        """Convenience: Keep track of the number of compact rolls performed on each server."""
        self.__increment("Initiative_Rolls", guild)


    def increment_stats_calculated(self, guild):
        """Convenience: Keeps track of the total stats invocations."""
        self.__increment("Stats_Calculated", guild)
