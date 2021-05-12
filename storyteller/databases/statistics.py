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
        # Make sure the guild isn't already in the table
        query = "SELECT * FROM GuildStats WHERE ID=%s;"
        self._execute(query, guildid)
        result = self.cursor.fetchone()

        if result is None:
            query = "INSERT INTO GuildStats VALUES (%s, %s);"
            self._execute(query, guildid, guildname)


    def rename_guild(self, guildid, name):
        """Updates the name of a guild in the GuildStats table."""
        query = "UPDATE GuildStats SET Name=%s WHERE ID=%s;"
        self._execute(query, name, guildid)


    def increment_rolls(self, guildid):
        """Keep track of the number of rolls performed on each server."""
        query = _increment_query("Rolls")
        self._execute(query, guildid)


    def increment_compact_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = _increment_query("Compact_Rolls")
        self._execute(query, guildid)


    def increment_traditional_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = _increment_query("Traditional_Rolls")
        self._execute(query, guildid)


    def increment_initiative_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = _increment_query("Initiative_Rolls")
        self._execute(query, guildid)

    def increment_stats_calculated(self, guildid):
        """Keeps track of the total stats invocations."""
        query = _increment_query("Stats_Calculated")
        self._execute(query, guildid)


def _increment_query(field):
    """Generates the increment query for a given field."""
    return f"UPDATE GuildStats SET {field} = {field} + 1 WHERE ID=%s;"
