"""settings.py - Database for managing server settings."""

from collections import defaultdict
from distutils.util import strtobool

from .base import Database

class SettingsDB(Database):
    """Interface for setting and retrieving server parameters."""

    # Non-boolean keys
    DEFAULT_DIFF = "default_diff"
    PREFIX = "prefix"

    __PARAMETERS = {
        "use_compact": "Set the server to always use compact rolls.",
        "xpl_always": "If `true`, tens always explode.",
        "xpl_spec": "If `true`, specialty tens explode.",
        "no_double": "If `true`, tens will never count as double successes.",
        "always_double": "If `true`, tens will always count as double successes.",
        "nullify_ones": "If `true`, the `z` roll option causes ones to not subtract successes.",
        DEFAULT_DIFF: "The default difficulty for a pool-based roll.",
        PREFIX: "Defines the bot invocation prefix.",
    }

    def __init__(self):
        super().__init__()
        self.__all_settings = self.__fetch_all_settings()

    def __fetch_all_settings(self) -> dict:
        """Fetch settings for each server."""
        query_cols = ", ".join(self.available_parameters)
        query = f"SELECT ID, {query_cols} FROM Guilds;"
        self._execute(query, ())
        results = self.cursor.fetchall()

        default_params = defaultdict(lambda: False)
        default_params[self.DEFAULT_DIFF] = 6
        default_params[self.PREFIX] = None
        settings = defaultdict(lambda: default_params)

        for row in results:
            row = list(row)
            guild = row.pop(0)

            parameters = {}
            for i, param in enumerate(self.available_parameters):
                parameters[param] = row[i]

            settings[guild] = parameters

        return settings

    def settings_for_guild(self, guild) -> dict:
        """Fetch the settings for a specific server."""
        if guild and not isinstance(guild, int):
            guild = guild.id

        return self.__all_settings[guild]

    def get_prefixes(self, guild) -> tuple:
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
        self._execute(query, (value, guild,))
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
            return ", ".join(self.get_prefixes(guild))

        return self.__all_settings[guild][key]

    @property
    def available_parameters(self):
        """Returns a list of available configuration options."""
        return self.__PARAMETERS.keys()

    def parameter_information(self, param) -> str:
        """Returns a description of what a given parameter does."""
        try:
            return self.__PARAMETERS[param]
        except KeyError:
            return f"Unknown parameter `{param}`!"

    def __validated_parameter(self, key, new_value):
        """Returns the proper value type for the parameter, or None."""
        if key not in self.available_parameters:
            raise ValueError(f"Unknown setting `{key}`!")

        if key == self.DEFAULT_DIFF:
            try:
                new_value = int(new_value)
                if not 2 <= new_value <= 10:
                    raise ValueError
                return new_value
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
