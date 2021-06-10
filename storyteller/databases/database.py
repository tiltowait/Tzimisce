"""database.py - Database handler for rolls stored rolls."""

# Historical note:
#
# This module is one of the oldest in the codebase. Initially, there was no
# separate database class; everything was handled by a single bot class. When
# this class was made, it was the only database class and handled multiple
# duties rather than focusing only on the SavedRolls table. This is why it has
# the seemingly special name of "database" rather than what would be the more
# standard "MacroDB". It also predates the use of the term "macro", which was
# coined by one of the bot's earliest users, which is why the clumsy references
# to "stored rolls" instead of macros. At some point in the future, a namespace
# cleanup will be done to rectify this inconsistency.

import re
from typing import Optional

import storyteller.parse
from .base import Database


class RollDB(Database):
    """Handles stored rolls, including creation, deletion, listing, and modification."""

    def __init__(self):
        super().__init__()

        # The foreign key constraint means that if the bot is removed from a
        # guild (or the guild is deleted), all associated macros will be removed
        # as well, to free up space. Additionally, it should be noted that the
        # metamacros table has its own constraint set on the macro_id field such
        # that when a macro is removed, so too are all metamacro entries
        # referencing it.
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS SavedRolls(
                ID       bigint NOT NULL,
                Name     Text   NOT NULL,
                Syntax   Text   NOT NULL,
                Guild    bigint NOT NULL,
                Comment  Text   NULL,
                macro_id int GENERATED ALWAYS AS IDENTITY,
                PRIMARY KEY(macro_id),
                CONSTRAINT fk_guild
                    FOREIGN KEY (Guild)
                        REFERENCES GuildSettings(ID)
                        ON DELETE CASCADE
            );
            """
        )

        # Install trigrams to enable fuzzy string matching on macro names
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        # Various syntax-matching regex patterns
        self.storex = re.compile(r"^(?P<name>[\w-]+)\s*=\s*(?P<syntax>.+)$")
        self.commentx = re.compile(r"^(?P<name>[\w-]+)\s+c=\s*(?P<comment>.*)$")
        self.usex = re.compile(r"^(?P<name>[\w-]+)\s*(?P<mods>(?P<sign>[+-])?\d+(?:\s[+-]?\d+)?)?$")
        self.deletex = re.compile(r"^(?P<name>[\w-]+)\s*=$")
        self.multiwordx = re.compile(r"[\w-]+ [\w-]+")


    def query_saved_rolls(self, guild: int, userid: int, command: dict):
        """
        Determines the type of query, then performs the necessary actions. This
        method creates, updates, retrieves, and deletes macros, and will even
        attempt to find a matching macro name if the one given doesn't match
        anything in the database.
        Args:
            guild (int): The Discord ID of the guild where bot was invoked
            userid (int): The Discord ID of the invoking user
            command (dict): A defaultdict(lambda: None). "syntax" is the most important key
        Returns: A notification string or an updated, macro-expanded command
        """
        syntax = command["syntax"]
        comment = command["comment"]

        # Store a new roll or change an old one.
        match = self.storex.match(syntax)
        if match:
            syntax = match.group("syntax")
            if storyteller.parse.is_valid_roll(syntax):
                name = match.group("name")
                return self.__store_roll(guild, userid, name, syntax, comment)
            return f"Sorry, `{syntax}` is invalid roll syntax!"

        # Change the comment of a stored roll
        match = self.commentx.match(syntax)
        if match:
            name = match.group("name")
            comment = match.group("comment")
            return self.__update_stored_comment(guild, userid, name, comment)

        # Use a stored roll.
        match = self.usex.match(syntax)
        if match:
            command = self.__match_stored_roll(command, match, guild, userid)
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


    def __match_stored_roll(self, command: dict, match: re.Match, guild: int, userid: int):
        """
        Retrieve and optionally modify a macro from the database.
        Args:
            command (dict): The command containing invocation context
            match (re.Match): The pregenerated regex match for easy syntax parsing
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the user who owns the macro
        Returns: A macro-expanded command, or an error string if unsuccessful
        """
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

            # Set the recalculated pool
            syntax[0] = str(int(syntax[0]) + pool_mod)

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


    def macro_count(self, guildid: int, userid: int) -> int:
        """
        Retrieve the number of macros associated with the user and guild.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
        Returns (int): The number of macros owned by the user
        """
        # Get the macro count
        query = "SELECT COUNT(*) FROM SavedRolls WHERE Guild=%s AND ID=%s;"
        self._execute(query, guildid, userid)
        macro_count = self.cursor.fetchone()[0]

        return macro_count


    def __store_roll(self, guild: int, userid: int, name: str, syntax: str, comment: str):
        """
        Store a new roll or update an old one.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
            name (str): The name of the macro to store/update
            syntax (str): The macro's syntax
            comment (str): The comment to associate with the macro
        """
        # pylint: disable=too-many-arguments

        # Inserting a new macro
        if not self.__is_roll_stored(guild, userid, name):
            # Create the roll
            query = "INSERT INTO SavedRolls VALUES (%s, %s, %s, %s, %s);"
            self._execute(query, userid, name, syntax, guild, comment)

            return f"Saved new macro: `{name}`."

        # UPDATING AN OLD MACRO

        # Updating both syntax and comment
        if comment:
            query = """
                UPDATE SavedRolls
                SET Syntax=%s, Comment=%s
                WHERE ID=%s AND Guild=%s AND Name ILIKE %s;
            """
            self._execute(query, syntax, comment, userid, guild, name)

            return f"Updated `{name}` syntax and comment."

        # Update only the syntax
        query = "UPDATE SavedRolls SET Syntax=%s WHERE ID=%s AND Guild=%s AND Name ILIKE %s;"
        self._execute(query, syntax, userid, guild, name)

        return f"Updated `{name}` syntax."


    def __update_stored_comment(self, guild: int, userid: int, name: str, comment: str) -> str:
        """
        Set or delete a stored roll's comment.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
            name (str): The name of the macro to modify
            comment (str): The comment to add
        Returns (str): A confirmation message
        """
        if self.__is_roll_stored(guild, userid, name):
            if len(comment) == 0:
                comment = None

            query = "UPDATE SavedRolls SET Comment=%s WHERE ID=%s AND Guild=%s AND Name ILIKE %s;"
            self._execute(query, comment, userid, guild, name)

            return f"Updated comment for `{name}`."

        return f"Unable to update. You don't have a roll named `{name}`!"


    def retrieve_stored_roll(self, guild: int, userid: int, name: str) -> Optional[tuple]:
        """
        Retrieve a macro's syntax.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
            name (str): The name of the macro to retrieve
        Returns (Optional[tuple]): The macro's syntax and comment
        """
        query = "SELECT Syntax, Comment FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self._execute(query, guild, userid, name)
        result = self.cursor.fetchone()

        return result


    def __find_similar_macro(self, guild: int, userid: int, name: str) -> Optional[str]:
        """
        Find a macro with a similar name to the one given. This method makes use
        of trigrams and is meant to be used when no exact match has been found.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
            name (str): The name of the macro whose likeness we are trying to find
        Returns (Optional[str]): The closest matching macro name
        """
        query = "SELECT Name FROM SavedRolls WHERE Guild=%s AND ID=%s AND SIMILARITY(Name, %s)>0.2;"
        self._execute(query, guild, userid, name)
        result = self.cursor.fetchone()

        if result:
            return result[0]

        return None


    def delete_stored_roll(self, guild: int, userid: int, name: str) -> str:
        """
        Delete a user's macro.
        Args:
            guild (int): The Discord ID of the guild associated with the macro
            userid (int): The Discord ID of the invoking user
            name (str): The name of the macro to delete
        Returns (str): A status message
        """
        if not self.__is_roll_stored(guild, userid, name):
            return f"Can't delete. `{name}` not found!"

        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self._execute(query, guild, userid, name)

        return f"`{name}` deleted! It has also been removed from any meta-macros containing it."


    def delete_user_rolls(self, guild: int, userid: int):
        """
        Delete all of a user's rolls in a given guild.
        Args:
            guild (int): The Discord ID of the guild from which to delete the macros
            userid (int): The Discord ID of the user whose macros will be deleted
        """
        query = "DELETE FROM SavedRolls WHERE Guild=%s AND ID=%s;"
        self._execute(query, guild, userid)


    def stored_rolls(self, guild: int, userid: int) -> list:
        """
        Retrieve a list of all the user's macros in a given guild.
        Args:
            guild (int): The Discord ID of the guild from which to retrieve the macros
            userid (int): The Discord ID of the user whose macros we will fetch
        Returns (list): A list of tuples of type: (macro name, syntax)
        """
        query = """SELECT Name, Syntax, Comment FROM SavedRolls WHERE Guild=%s AND ID=%s
                   ORDER BY Name;"""
        self._execute(query, guild, userid)
        results = self.cursor.fetchall()

        fields = []
        for row in results:
            name = row[0]
            syntax = row[1]
            comment = row[2]

            if comment:
                syntax += f" # {comment}"

            fields.append((name, syntax))

        return fields


    def __is_roll_stored(self, guild: int, userid: int, name: str) -> bool:
        """
        Determine whether the user has a specific macro in a given guild.
        Args:
            guild (int): The Discord ID of the guild from which to search
            userid (int): The Discord ID of the user performing the search
            name (str): The name of the macro to search for
        """
        return self.retrieve_stored_roll(guild, userid, name) is not None
