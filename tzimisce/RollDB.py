"""Database handler for rolls stored rolls."""

import os
import re
import psycopg2


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

        # This table is just used for statistics purposes.
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Guilds
                              (ID    bigint PRIMARY KEY,
                               NAME  Text   NOT NULL,
                               Rolls int    NOT NULL DEFAULT 0);"""
        )

        # Install trigrams
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        self.conn.commit()

    def execute(self, query, args):
        """Executes the specified query. Tries to reconnect to the database if there's an error."""
        try:
            self.cursor.execute(query, args)
        except psycopg2.errors.AdminShutdown:
            # Connection got reset for some reason, so fix it
            print("Database lost connection. Retrying.")
            self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, args) # Reconnected, so try again!

    def query_saved_rolls(self, guild, userid, command):
        """Parses the message to see what kind of query is needed, then performs it."""
        syntax = command["syntax"]
        comment = command["comment"]

        # Store a new roll or change an old one.
        pattern = re.compile(
            r"^(?P<name>[\w-]+)\s*=\s*(?P<syn>\d+\s*\d*\s*.*|\d+(d\d+)?(\+(\d+|\d+d\d+))*)$"
        )
        match = pattern.match(syntax)
        if match:
            name = match.group("name")
            syntax = match.group("syn")
            return self.store_roll(guild, userid, name, syntax, comment)

        # Change the comment of a stored roll
        pattern = re.compile(r"^(?P<name>[\w-]+)\s+c=(?P<comment>.*)$")
        match = pattern.match(syntax)
        if match:
            name = match.group("name")
            comment = match.group("comment")
            return self.update_stored_comment(guild, userid, name, comment)

        # Use a stored roll.
        pattern = re.compile(
            r"^(?P<name>[\w-]+)\s*(?P<mods>(?:0|[+-]\d+)(?:\s+[+-]?\d+)?)?$"
        )
        match = pattern.match(syntax)
        if match:
            name = match.group("name")
            compound = self.retrieve_stored_roll(guild, userid, name)

            if not compound:
                alt = self.__find_similar_macro(guild, userid, name)
                if alt:
                    return f"`{name}` not found. Did you mean `{alt[0]}`?"

                return f"Sorry, `{name}` doesn't exist!"

            syntax = compound[0]
            mods = match.group("mods")

            # Mods can modify a stored roll by changing the pool, diff, or both
            if mods:
                mods = mods.split()
                pool_mod = int(mods[0])

                # Modify the pool first
                syntax = syntax.split()
                if len(syntax) == 1: # Need a default difficulty
                    syntax.append(6)
                elif len(syntax) == 2:
                    if not syntax[1][0].isdigit(): # it's a specialty
                        syntax.insert(1, 6)

                current_pool = int(syntax[0])
                syntax[0] = str(current_pool + pool_mod)

                # Modify or replace the difficulty
                diff_mod = "+0"
                if len(mods) == 2: # diff mod is optional; unchanged if omitted
                    diff_mod = mods[1]

                if diff_mod.isdigit():
                    syntax[1] = diff_mod
                else:
                    current_diff = int(syntax[1])
                    syntax[1] = str(current_diff + int(diff_mod))

                syntax = " ".join(syntax)

            # Write the new command
            command["syntax"] = syntax
            if compound[1] and not command["comment"]:
                command["comment"] = compound[1]

            return command

        # Delete a stored roll.
        match = re.match(r"^(?P<name>[\w-]+)\s*=$", syntax)
        if match:
            name = match.group("name")
            return self.delete_stored_roll(guild, userid, name)

        # We have no idea what the user wanted to do.
        return "Come again?"

    def store_roll(self, guild, userid, name, syntax, comment):
        """Store a new roll, or update an old one."""
        if not self.__is_roll_stored(guild, userid, name):
            # Create the roll
            query = "INSERT INTO SavedRolls VALUES (%s, %s, %s, %s, %s);"
            self.execute(query, (userid, name, syntax, guild, comment,))
            self.conn.commit()

            return f"Saved new macro: `{name}`."

        # Update an old roll
        if comment:
            query = "UPDATE SavedRolls SET Syntax=%s, Comment=%s WHERE ID=%s AND Name ~* %s;"
            self.execute(query, (syntax, comment, userid, name,))
            self.conn.commit()

            return f"Updated `{name}` syntax and comment."
        else:
            query = "UPDATE SavedRolls SET Syntax=%s WHERE ID=%s AND Name ~* %s;"
            self.execute(query, (syntax, userid, name,))
            self.conn.commit()

            return f"Updated `{name}` syntax."

    def update_stored_comment(self, guild, userid, name, comment):
        """Set or delete a stored roll's comment"""
        if self.__is_roll_stored(guild, userid, name):
            comment = comment.strip()
            if len(comment) == 0:
                comment = None

            query = "UPDATE SavedRolls SET Comment=%s WHERE ID=%s AND Name ~* %s;"
            self.execute(query, (comment, userid, name,))
            self.conn.commit()

            return f"Updated comment for `{name}`."

        return "Roll not found!"

    def retrieve_stored_roll(self, guild, userid, name):
        """Returns the Syntax for a stored roll."""
        query = "SELECT Syntax, Comment FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ~* %s;"
        self.execute(query, (guild, userid, name,))
        result = self.cursor.fetchone()

        return result

    def __find_similar_macro(self, guild, userid, name):
        query = "SELECT Name FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name %% %s;"
        self.execute(query, (guild, userid, name,))
        result = self.cursor.fetchone()

        return result

    def delete_stored_roll(self, guild, userid, name):
        """Delete a stored roll."""
        if not self.__is_roll_stored(guild, userid, name):
            return f"Can't delete. `{name}` not found!"

        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ~* %s;"
        self.execute(query, (guild, userid, name,))
        self.conn.commit()

        return f"`{name}` deleted!"

    def delete_user_rolls(self, guild, userid):
        """Deletes all of a user's rolls on a given guild."""
        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s;"
        self.execute(query, (guild, userid,))
        self.conn.commit()

    def stored_rolls(self, guild, userid):
        """Returns an list of all the stored rolls."""
        query = "SELECT Name, Syntax FROM SavedRolls WHERE Guild=%s AND ID=%s ORDER BY Name;"
        self.execute(query, (guild, userid,))
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

        self.execute(query, (guildid, name,))
        self.conn.commit()

    def remove_guild(self, guildid):
        """Removes a guild from the Guilds table."""
        query = "DELETE FROM Guilds WHERE ID=%s;"

        self.execute(query, (guildid,))
        self.conn.commit()

    def rename_guild(self, guildid, name):
        """Updates the name of a guild in the Guilds table."""
        query = "UPDATE Guilds SET Name=%s WHERE ID=%s;"

        self.execute(query, (name, guildid,))
        self.conn.commit()

    def increment_rolls(self, guildid):
        """Keep track of the number of rolls performed on each server."""
        query = "UPDATE Guilds SET Rolls = Rolls + 1 WHERE ID=%s;"

        self.execute(query, (guildid,))
        self.conn.commit()
