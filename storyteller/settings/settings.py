"""settings.py - Database for managing server settings."""

import os
from collections import defaultdict
from distutils.util import strtobool

import psycopg2

class SettingsDB:
    """Interface for setting and retriving server parameters."""

    # Keys
    COMPACT = "use_compact"
    EXPLODE_ALWAYS = "xpl_always"
    EXPLODE_SPEC = "xpl_spec"
    NO_DOUBLE = "no_double"
    ALWAYS_DOUBLE = "always_double"
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
                   default_diff, always_double FROM Guilds;"""
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
            always_double = row.pop(0)

            params = {
                "use_compact": compact,
                "xpl_always": explode_always,
                "xpl_spec": explode_spec,
                "no_double": no_double,
                self.ALWAYS_DOUBLE: always_double,
                "nullify_ones": nullify_ones,
                "default_diff": default_diff,
                "prefix": prefix
            }
            settings[guild] = params

        return settings

    def settings_for_guild(self, guild) -> dict:
        """Fetch the settings for a specific server."""
        if guild and not isinstance(guild, int):
            guild = guild.id

        return self.__all_settings[guild]

    def get_prefix(self, guild) -> tuple:
        """Returns the guild's prefix. If the guild is None, returns a default."""
        if guild and not isinstance(guild, int):
            guild = guild.id

        prefix = self.settings_for_guild(guild)[SettingsDB.PREFIX]
        if prefix:
            return (prefix,)
        return ("!", "/")

    def update(self, guild, key, value) -> str:
        """Sets a server parameter."""
        value = self.__validated_parameter(key, value) # Raises ValueError if invalid

        # Normally unsafe, but we do input validation before we get here
        query = f"UPDATE Guilds SET {key}=%s WHERE ID=%s;"
        self.__execute(query, (value, guild,))
        self.__all_settings[guild][key] = value

        message = f"Setting `{key}` to `{value}`!"
        if key == self.PREFIX:
            if value:
                message = f"Setting the prefix to `{value}m`."
                if len(value) > 3:
                    message += " A prefix this long might be annoying to type!"
            else:
                message = "Reset the command prefix to `/m` and `!m`."

        return message

    def value(self, guild, key):
        """Retrieves a value for a specific key for a given guild."""
        if key not in self.available_parameters:
            raise ValueError(f"Unknown setting `{key}`!")

        if key == SettingsDB.PREFIX:
            return ", ".join(self.get_prefix(guild))

        return self.__all_settings[guild][key]

    @property
    def available_parameters(self):
        """Returns a list of available configuration options."""
        return [
            self.COMPACT, self.EXPLODE_ALWAYS, self.EXPLODE_SPEC, self.NO_DOUBLE, self.NULLIFY_ONES,
            self.DEFAULT_DIFF, self.ALWAYS_DOUBLE, self.PREFIX
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
        if param == self.ALWAYS_DOUBLE:
            return "If `true`, tens will count as double successes regardless of specialty."
        if param == self.PREFIX:
            return "Defines the bot invokation prefix."

        return "Unknown parameter!"

    def __validated_parameter(self, key, new_value):
        """Returns the proper value type for the parameter, or none."""
        if key not in self.available_parameters:
            raise ValueError(f"Unknown setting `{key}`!")

        if key == self.DEFAULT_DIFF:
            try:
                new_value = int(new_value)
                if 2 <= new_value <= 10:
                    return new_value
                raise ValueError
            except ValueError:
                raise ValueError(f"Error! `{key}` must be an integer between 2-10.") from None
        if key == self.PREFIX:
            return new_value

        # All other keys are true/false
        try:
            new_value = bool(strtobool(new_value))
            return new_value
        except ValueError:
            raise ValueError(f"Error! `{key}` must be `true` or `false`!") from None
