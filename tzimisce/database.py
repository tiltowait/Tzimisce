"""Database handler for rolls stored rolls."""

import os
import re
from collections import defaultdict

import psycopg2
from tzimisce.initiative import InitiativeManager

class RollDB:
    """Handles stored rolls, including creation, deletion, listing, and modification."""

    def __init__(self):
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
        self.cursor = self.conn.cursor()

        # The main table for storing rolls.
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS SavedRolls
                              (ID      bigint NOT NULL,
                               Name    Text   NOT NULL,
                               Syntax  Text   NOT NULL,
                               Guild   bigint NOT NULL,
                               Comment Text   NULL);"""
        )

        # The initiative table(s)
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Initiative
                              (Channel   bigint NOT NULL,
                               Character Text NOT NULL,
                               Mod       int NOT NULL,
                               Die       int NOT NULL);"""
        )

        # This table is just used for statistics purposes.
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Guilds
                              (ID                bigint PRIMARY KEY,
                               NAME              Text   NOT NULL,
                               Rolls             int    NOT NULL DEFAULT 0,
                               Prefix            Text,
                               Compact_Rolls     int    NOT NULL DEFAULT 0,
                               Traditional_Rolls int    NOT NULL DEFAULT 0,
                               Initiative_Rolls  int    NOT NULL DEFAULT 0);"""
        )

        # Install trigrams
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        self.conn.commit()

        # Macro patterns
        self.storex = re.compile(
            r"^(?P<name>[\w-]+)\s*=\s*(?P<syn>\d+\s*\d*\s*.*|\d+(d\d+)?(\+(\d+|\d+d\d+))*)$"
        )
        self.commentx = re.compile(r"^(?P<name>[\w-]+)\s+c=(?P<comment>.*)$")
        self.usex = re.compile(r"^(?P<name>[\w-]+)\s*(?P<mods>(?P<sign>[+-])?\d+(?:\s[+-]?\d+)?)?$")
        self.deletex = re.compile(r"^(?P<name>[\w-]+)\s*=$")
        self.multiwordx = re.compile(r"[\w-]+ [\w-]+")

    def __execute(self, query, args):
        """Executes the specified query. Tries to reconnect to the database if there's an error."""
        try:
            self.cursor.execute(query, args)
        except psycopg2.errors.AdminShutdown: # pylint: disable=no-member
            # Connection got reset for some reason, so fix it
            print("Lost database connection. Retrying.")
            self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, args) # Reconnected, so try again!

    def query_saved_rolls(self, guild, userid, command):
        """Parses the message to see what kind of query is needed, then performs it."""
        syntax = command["syntax"]
        comment = command["comment"]

        # Store a new roll or change an old one.
        match = self.storex.match(syntax)
        if match:
            name = match.group("name")
            syntax = match.group("syn")
            return self.__store_roll(guild, userid, name, syntax, comment)

        # Change the comment of a stored roll
        match = self.commentx.match(syntax)
        if match:
            name = match.group("name")
            comment = match.group("comment")
            return self.__update_stored_comment(guild, userid, name, comment)

        # Use a stored roll.
        match = self.usex.match(syntax)
        if match:
            name = match.group("name")
            compound = self.retrieve_stored_roll(guild, userid, name)

            if not compound:
                alt = self.__find_similar_macro(guild, userid, name)
                if alt:
                    return f"`{name}` not found. Did you mean `{alt}`?"

                return f"Sorry, you have no macro named `{name}`!"

            syntax = compound[0]
            mods = match.group("mods")

            # The user may modify a stored roll by changing the pool, diff, or both
            if mods:
                mods = mods.split()
                pool_mod = int(mods[0])

                if pool_mod != 0 and not match.group("sign"):
                    return "Pool modifiers must be zero or have a +/- sign."

                pool_desc = f"Pool {pool_mod:+}. " if pool_mod != 0 else ""

                # Modify the pool first
                syntax = syntax.split()
                if len(syntax) == 1 or not syntax[1][0].isdigit(): # Need a default difficulty
                    syntax.insert(1, 6)

                new_pool = int(syntax[0]) + pool_mod
                syntax[0] = str(new_pool)

                # Modify or replace the difficulty
                diff_desc = ""
                diff_mod = "+0" if len(mods) < 2 else mods[1]

                if diff_mod.isdigit(): # No +/- sign
                    syntax[1] = diff_mod
                    diff_desc = f"Diff. to {diff_mod}."
                else:
                    diff_mod = int(diff_mod)
                    current_diff = int(syntax[1])
                    syntax[1] = str(current_diff + diff_mod)

                    if diff_mod != 0:
                        diff_desc = f"Diff. {diff_mod:+}."

                command["override"] = f"{pool_desc}{diff_desc}" # Notice of override

                syntax = " ".join(syntax)

            # Only use the stored command if a new one isn't given
            command["syntax"] = syntax
            if compound[1] and not command["comment"]:
                command["comment"] = compound[1]

            return command

        # Delete a stored roll.
        match = self.deletex.match(syntax)
        if match:
            name = match.group("name")
            return self.delete_stored_roll(guild, userid, name)

        # See if the user tried to do a multi-word macro
        if self.multiwordx.match(syntax):
            return "Sorry, macro names can't contain spaces!"

        # We have no idea what the user wanted to do.
        return "Come again?"

    def __store_roll(self, guild, userid, name, syntax, comment):
        """Store a new roll, or update an old one."""
        # pylint: disable=too-many-arguments

        # Inserting a new macro
        if not self.__is_roll_stored(guild, userid, name):
            # Create the roll
            query = "INSERT INTO SavedRolls VALUES (%s, %s, %s, %s, %s);"
            self.__execute(query, (userid, name, syntax, guild, comment,))
            self.conn.commit()

            return f"Saved new macro: `{name}`."

        # Updating an old macro

        # Updating both syntax and comment
        if comment:
            query = """
                UPDATE SavedRolls
                SET Syntax=%s, Comment=%s
                WHERE ID=%s AND Guild=%s AND Name ILIKE %s;
            """
            self.__execute(query, (syntax, comment, userid, guild, name,))
            self.conn.commit()

            return f"Updated `{name}` syntax and comment."

        # Update only syntax
        query = "UPDATE SavedRolls SET Syntax=%s WHERE ID=%s AND Guild=%s AND Name ILIKE %s;"
        self.__execute(query, (syntax, userid, guild, name,))
        self.conn.commit()

        return f"Updated `{name}` syntax."

    def __update_stored_comment(self, guild, userid, name, comment):
        """Set or delete a stored roll's comment"""
        if self.__is_roll_stored(guild, userid, name):
            comment = comment.strip()
            if len(comment) == 0:
                comment = None

            query = "UPDATE SavedRolls SET Comment=%s WHERE ID=%s AND Guild=%s AND Name ILIKE %s;"
            self.__execute(query, (comment, userid, guild, name,))
            self.conn.commit()

            return f"Updated comment for `{name}`."

        return f"Unable to update. You don't have a roll named `{name}`!"

    def retrieve_stored_roll(self, guild, userid, name):
        """Returns the Syntax for a stored roll."""
        query = "SELECT Syntax, Comment FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self.__execute(query, (guild, userid, name,))
        result = self.cursor.fetchone()

        return result

    def __find_similar_macro(self, guild, userid, name):
        query = "SELECT Name FROM SavedRolls WHERE Guild=%s AND ID=%s AND SIMILARITY(Name, %s)>0.2;"
        self.__execute(query, (guild, userid, name,))
        result = self.cursor.fetchone()

        if result:
            return result[0]

        return None

    def delete_stored_roll(self, guild, userid, name):
        """Delete a stored roll."""
        if not self.__is_roll_stored(guild, userid, name):
            return f"Can't delete. `{name}` not found!"

        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self.__execute(query, (guild, userid, name,))
        self.conn.commit()

        return f"`{name}` deleted!"

    def delete_user_rolls(self, guild, userid):
        """Deletes all of a user's rolls on a given guild."""
        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s;"
        self.__execute(query, (guild, userid,))
        self.conn.commit()

    def stored_rolls(self, guild, userid):
        """Returns an list of all the stored rolls."""
        query = "SELECT Name, Syntax FROM SavedRolls WHERE Guild=%s AND ID=%s ORDER BY Name;"
        self.__execute(query, (guild, userid,))
        results = self.cursor.fetchall()

        fields = []
        for row in results:
            fields.append((row[0], row[1]))

        return fields

    def __is_roll_stored(self, guild, userid, name):
        """Returns true if a roll by the given name has been stored."""
        return self.retrieve_stored_roll(guild, userid, name) is not None

    def add_guild(self, guildid, name):
        """Adds a guild to the Guilds table."""
        query = "INSERT INTO Guilds VALUES (%s, %s);"

        self.__execute(query, (guildid, name,))
        self.conn.commit()

    def remove_guild(self, guildid):
        """Removes a guild from the Guilds table."""
        query = "DELETE FROM Guilds WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()

    def rename_guild(self, guildid, name):
        """Updates the name of a guild in the Guilds table."""
        query = "UPDATE Guilds SET Name=%s WHERE ID=%s;"

        self.__execute(query, (name, guildid,))
        self.conn.commit()

    def increment_rolls(self, guildid):
        """Keep track of the number of rolls performed on each server."""
        query = "UPDATE Guilds SET Rolls = Rolls + 1 WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()

    def increment_compact_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = "UPDATE Guilds SET Compact_Rolls = Compact_Rolls + 1 WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()

    def increment_traditional_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = "UPDATE Guilds SET Traditional_Rolls = Traditional_Rolls + 1 WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()

    def increment_initiative_rolls(self, guildid):
        """Keep track of the number of compact rolls performed on each server."""
        query = "UPDATE Guilds SET Initiative_Rolls = Initiative_Rolls + 1 WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()


    # Prefix stuff

    def get_all_prefixes(self):
        """Returns a dictionary of all guild command prefixes."""
        query = "SELECT ID, Prefix FROM Guilds;"

        self.__execute(query, ())

        prefixes = defaultdict(lambda: None)
        prefixes.update(dict(self.cursor.fetchall()))

        return prefixes

    def update_prefix(self, guildid, prefix):
        """Update the bot's command prefix for a given guild."""
        query = "UPDATE Guilds SET Prefix = %s WHERE ID=%s;"

        self.__execute(query, (prefix, guildid,))
        self.conn.commit()


    # Initiative Stuff

    def suggested_initiative(self, guildid):
        """Keep track of number of times initiative manager has been suggested."""
        query = "UPDATE Guilds SET initiative_suggestions=initiative_suggestions+1 WHERE ID=%s;"

        self.__execute(query, (guildid,))
        self.conn.commit()

    def set_initiative(self, channel, character, mod, die):
        """Adds an initiative record."""
        self.remove_initiative(channel, character)

        query = "INSERT INTO Initiative VALUES (%s, %s, %s, %s);"

        self.__execute(query, (channel, character, mod, die,))
        self.conn.commit()

    def set_initiative_action(self, channel, character, action):
        """Stores the declared action for a character."""
        query = "UPDATE Initiative SET Action=%s WHERE Channel=%s AND Character=%s;"

        self.__execute(query, (action, channel, character))
        self.conn.commit()

    def remove_initiative(self, channel, character):
        """Removes a character from a given channel."""
        query = "DELETE FROM Initiative WHERE Channel=%s AND Character=%s;"

        self.__execute(query, (channel, character,))
        self.conn.commit()

    def clear_initiative(self, channel):
        """Removes all initiative records from a given channel."""
        query = "DELETE FROM Initiative WHERE Channel=%s;"

        self.__execute(query, (channel,))
        self.conn.commit()

    def get_initiative_tables(self):
        """Returns a dictionary of all initiatives."""
        query = "SELECT Channel, Character, Mod, Die, Action FROM Initiative ORDER BY Channel;"

        self.__execute(query, ())
        managers = defaultdict(lambda: None)

        for channel, character, mod, die, action in self.cursor.fetchall():
            manager = managers[channel]
            if not manager:
                manager = InitiativeManager()
                managers[channel] = manager

            manager.add_init(character, mod, die, action)

        return managers
