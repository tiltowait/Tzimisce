"""settings.py - Database for managing server settings."""

import os
from collections import defaultdict
import psycopg2

class SettingsDB:
    """Interface for setting and retriving server parameters."""

    # Keys
    COMPACT = "use_compact"
    EXPLODE_ALWAYS = "xpl_always"
    EXPLODE_SPEC = "xpl_spec"
    NO_DOUBLE = "no_double"
    NULLIFY_ONES = "nullify_ones"
    DEFAULT_DIFF = "default_diff"
    PREFIX = "prefix"

    def __init__(self):
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        self.__all_settings = self.__fetch_all_settings()

    def __execute(self, query, args):
        """Executes the specified query. Tries to reconnect to the database if there's an error."""
        try:
            self.cursor.execute(query, args)
        except psycopg2.errors.AdminShutdown: # pylint: disable=no-member
            # Connection got reset for some reason, so fix it
            print("Lost database connection. Retrying.")
            self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, args) # Reconnected, so try again!

    def __fetch_all_settings(self) -> dict:
        """Fetch settings for each server."""

        query = """SELECT ID, use_compact, nullify_ones, prefix, xpl_always, xpl_spec, no_double,
                   default_diff FROM Guilds;"""
        self.__execute(query, ())
        results = self.cursor.fetchall()

        default_params = defaultdict(lambda: False)
        settings = defaultdict(lambda: default_params)

        for row in results:
            row = list(row)

            guild = row.pop(0)
            compact = row.pop(0)
            nullify_ones = row.pop(0)
            prefix = row.pop(0)
            explode_always = row.pop(0)
            explode_spec = row.pop(0)
            no_double = row.pop(0)
            default_diff = row.pop(0)

            params = {
                "use_compact": compact,
                "xpl_always": explode_always,
                "xpl_spec": explode_spec,
                "no_double": no_double,
                "nullify_ones": nullify_ones,
                "default_diff": default_diff,
                "prefix": prefix
            }
            settings[guild] = params

        return settings

    def settings_for_guild(self, guild) -> dict:
        """Fetch the settings for a specific server."""

        return self.__all_settings[guild]

    def get_prefix(self, guild) -> tuple:
        """Returns the guild's prefix. If the guild is None, returns a default."""
        default_prefixes = ("!", "/")

        if not guild:
            return default_prefixes

        if not isinstance(guild, int):
            guild = guild.id

        prefix = self.settings_for_guild(guild)[SettingsDB.PREFIX]
        if prefix:
            return (prefix,)
        return default_prefixes

    def update(self, guild, key, value):
        """Sets a server parameter."""

        # Normally unsafe, but we do input validation before we get here
        query = f"UPDATE Guilds SET {key}=%s WHERE ID=%s;"
        self.__execute(query, (value, guild,))

        self.__all_settings[guild][key] = value

    def value(self, guild, key):
        """Retrieves a value for a specific key for a given guild."""
        if key == SettingsDB.PREFIX:
            return ", ".join(self.get_prefix(guild))

        return self.__all_settings[guild][key]

    def available_parameters(self):
        """Returns a list of available configuration options."""

        return [
            self.COMPACT, self.EXPLODE_ALWAYS, self.EXPLODE_SPEC, self.NO_DOUBLE, self.NULLIFY_ONES,
            self.DEFAULT_DIFF, self.PREFIX
        ]

    def parameter_information(self, param) -> str:
        """Returns a description of what a given parameter does."""
        # pylint: disable=too-many-return-statements

        if param == self.COMPACT:
            return "Set the server to always use compact rolls."
        if param == self.EXPLODE_ALWAYS:
            return "If `true`, tens always explode."
        if param == self.EXPLODE_SPEC:
            return "If `true`, specialty tens explode."
        if param == self.NO_DOUBLE:
            return "If `true`, tens never count as double successes."
        if param == self.NULLIFY_ONES:
            return "If `true`, the `z` roll option causes ones to not subtract successes."
        if param == self.DEFAULT_DIFF:
            return "The default difficulty for a pool-based roll."
        if param == self.PREFIX:
            return "Defines the bot invokation prefix."

        return "Unknown parameter!"
