"""settings.py - Database for managing server settings."""

from collections import defaultdict
from distutils.util import strtobool

from psycopg2.sql import SQL, Identifier

from .base import Database


class SettingsDB(Database):
    """Interface for setting and retrieving server parameters."""

    # "Interesting" keys that get specially referenced elsewhere
    DEFAULT_DIFF = "default_diff"
    PREFIX = "prefix"
    XPL_ALWAYS = "xpl_always"
    NEVER_DOUBLE = "never_double"
    IGNORE_ONES = "ignore_ones"
    NEVER_BOTCH = "never_botch"
    CHRONICLES = "chronicles"

    __PARAMETERS = {
        PREFIX: "Defines the bot invocation prefix.",
        "use_compact": "Set the server to always use compact rolls.",
        "unsort_rolls": "Dice are displayed in roll order vs. sorted.",
        DEFAULT_DIFF: "The default difficulty for a pool-based roll.",
        XPL_ALWAYS: "If `true`, tens always explode.",
        "xpl_spec": "If `true`, specialty tens explode.",
        NEVER_DOUBLE: "If `true`, tens will never count as double successes.",
        "always_double": "If `true`, tens will always count as double successes.",
        IGNORE_ONES: "If `true`, ones do not subtract from non-botching rolls.",
        NEVER_BOTCH: "Permanently disables botches.",
        "wp_cancelable": "Allows ones to cancel a Willpower success.",
        CHRONICLES: "Enables Chronicles of Darkness-style rolls."
    }

    # Though "sort_rolls" would be a more logical setting (and unsorted the default), for historical
    # reasons we're doing the opposite. In earlier versions, the bot only displayed dice in sorted
    # order. After conducting a small poll on the Discord server, it was decided to keep sorted as
    # the default, despite the slightly clunky language and logic inherent to "unsort_rolls".


    def __init__(self):
        super().__init__()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS GuildSettings(
                ID                bigint  PRIMARY KEY,
                Prefix            Text,
                use_compact       boolean DEFAULT FALSE,
                xpl_spec          boolean DEFAULT FALSE,
                ignore_ones       boolean DEFAULT FALSE,
                xpl_always        boolean DEFAULT FALSE,
                never_double      boolean DEFAULT FALSE,
                always_double     boolean DEFAULT FALSE,
                default_diff      int     DEFAULT 6,
                wp_cancelable     boolean DEFAULT FALSE,
                chronicles        boolean DEFAULT FALSE,
                never_botch       boolean DEFAULT FALSE,
                unsort_rolls        boolean DEFAULT FALSE
            );
            """
        )
        self.__all_settings = self.__fetch_all_settings() # Cache for performance reasons

        # Set up the default parameters
        self.default_params = defaultdict(lambda: False)
        self.default_params[self.DEFAULT_DIFF] = 6
        self.default_params[self.PREFIX] = None


    def __fetch_all_settings(self) -> dict:
        """
        Retrieves the settings for each server.
        Returns (dict): The settings for each server, with the Discord guild ID as the keys
        """
        fields = SQL(", ").join(map(Identifier, self.available_parameters))
        query = SQL("SELECT ID, {fields} FROM GuildSettings;").format(fields=fields)

        self._execute(query)
        results = self.cursor.fetchall()

        settings = defaultdict(lambda: self.default_params)

        # Put the fetched parameters into dictionaries
        for row in results:
            row = list(row)
            guild = row.pop(0)
            parameters = dict(zip(self.available_parameters, row))

            settings[guild] = parameters

        return settings


    def settings_for_guild(self, guild) -> dict:
        """
        Fetch the settings for a specific guild.
        Args:
            guild (int): The Discord ID of the guild
        Returns (dict): The guild's settings
        """
        if guild and not isinstance(guild, int):
            guild = guild.id

        # Make sure the settings are actually in the guild
        if guild is not None and guild not in self.__all_settings:
            print(f'Guild {guild} wasn\'t in GuildSettings! Adding now.')
            self.add_guild(guild)

        return self.__all_settings[guild]


    def get_prefixes(self, guild) -> tuple:
        """
        Retrieve the guild's prefixes.
        Args:
            guild (int): The guild's ID
        Returns (tuple): A tuple containing the guild's prefixes
        """
        if guild and not isinstance(guild, int):
            guild = guild.id

        prefix = self.settings_for_guild(guild)[SettingsDB.PREFIX]
        if prefix:
            return (prefix,)
        return ("!m", "/m")


    def update(self, guild, key, value) -> str:
        """
        Set a new value for one of a guild's parameters.
        Args:
            guild (int): The Discord ID of the guild to modify
            key (str): The parameter to modify
            value (any): The parameter's new value
        Returns (str): A message informing the user of the change
        """
        value = self.__validated_parameter(key, value) # Raises ValueError if invalid

        query = SQL("UPDATE GuildSettings SET {key}=%s WHERE ID=%s;").format(key=Identifier(key))
        self._execute(query, value, guild)
        self.__all_settings[guild][key] = value

        message = f"Setting `{key}` to `{value}`!"
        if key == self.PREFIX:
            if value:
                message = f"Setting the prefix to `{value}`."
                if len(value) > 3:
                    message += " A prefix this long might be annoying to type!"
            else:
                message = "Reset the command prefix to `/m` and `!m`."
        elif key == self.CHRONICLES:
            # Also set default difficulty, always explode, nullify ones, no botching
            self.update(guild, SettingsDB.DEFAULT_DIFF, 8 if value else 6)
            self.update(guild, SettingsDB.XPL_ALWAYS, str(value))
            self.update(guild, SettingsDB.IGNORE_ONES, str(value))
            self.update(guild, SettingsDB.NEVER_BOTCH, str(value))

            message = "Enabling" if value else "Disabling"
            message += " Chronicles of Darkness mode."

        return message


    def value(self, guild, key):
        """
        Retrieve a specific setting on a given guild.
        Args:
            guild (int): The guild's ID
            key (str): The parameter whose value is desired
        Returns (any): The current value for the parameter
        Raises: ValueError if key isn't a valid parameter
        """
        if key not in self.available_parameters:
            raise ValueError(f"Unknown setting `{key}`!")

        if key == SettingsDB.PREFIX:
            return ", ".join(self.get_prefixes(guild))

        return self.__all_settings[guild][key]


    def __validated_parameter(self, key, new_value):
        """
        Attempt to cast a value into the proper data type for the associated parameter.
        Args:
            key (str): The parameter being modified
            new_value (str): The value attempting to be stored
        Returns (any): new_value cast to the proper data type
        Raises: ValueError if new_value is an invalid type or value
        """
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


    @property
    def available_parameters(self):
        """Returns a list of available configuration options."""
        return self.__PARAMETERS.keys()


    def parameter_information(self, param: str) -> str:
        """
        Retrieve the description for a given parameter. Sends an error message if invalid.
        Args:
            param (str): The parameter whose details are requested
        Returns (str): The parameter descriptions, or an error message
        """
        try:
            return self.__PARAMETERS[param]
        except KeyError:
            return f"Unknown parameter `{param}`!"


    # Housekeeping stuff

    def add_guild(self, guildid: int):
        """
        Add a guild with default settings to the GuildSettings table.
        Args:
            guildid (int): The Discord ID of the guild to add
        """
        query = "INSERT INTO GuildSettings VALUES (%s);"
        self._execute(query, guildid)

        # Add the guild to the settings dictionary
        self.__all_settings[guildid] = self.default_params


    def remove_guild(self, guildid: int):
        """
        Remove a guild from the GuildSettings table.
        Args:
            guildid (int): The Discord ID of the guild to remove
        """
        query = "DELETE FROM GuildSettings WHERE ID=%s;"
        self._execute(query, guildid)
