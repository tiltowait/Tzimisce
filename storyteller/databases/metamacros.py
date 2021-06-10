"""metamacros.py - Defines a Database class for managing metamacros."""

from .base import Database


class MetaMacroDB(Database):
    """
    A database manager for handling metamacros.

    A metamacro is a special type of macro that calls other macros. Each
    metamacro comprises three or more records in a table, with an associated
    metamacro name and a reference to a MacroID, which is the ID (and primary
    key) of a macro defined in SavedRolls.
    """

    def __init__(self):
        super().__init__()

        # The foreign key constraint automatically removes metamacro records
        # when the referenced macro is deleted. This can result in a metamacro
        # with fewer than three entries; however, there is no compelling reason
        # for the bot to complain in this case, even if we mandate 3+ macros at
        # creation.
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS MetaMacros(
                GuildID  bigint NOT NULL,
                UserID   bigint NOT NULL,
                MetaName Text  NOT NULL,
                MacroID  int    NOT NULL,
                CONSTRAINT fk_macro
                     FOREIGN KEY(MacroID)
                         REFERENCES SavedRolls(macro_id)
                         ON DELETE CASCADE
            );
            """
        )


    def store_metamacro(self, guildid: int, userid: int, meta_name: str, *macros) -> bool:
        """
        Store a metamacro.
        Args:
            guildid (int): The Discord ID of the associated guild
            userid (int): The Discord ID of the user who owns the metamacro
            meta_name (str): The name of the new metamacro
            macros (*str): The macros comprising the metamacro
        Returns (bool): True if the user has just overwritten an old metamacro
        Raises: KeyError if one of the given macros doesn't exist
        """
        for macro in macros:
            if not self.__macro_exists(guildid, userid, macro):
                raise KeyError(f"Error! You don't have a macro named `{macro}`!")

        # There's no simple way to update a metamacro, so let's simply delete the old one
        overwriting = False
        if self.__metamacro_exists(guildid, userid, meta_name):
            self.delete_metamacro(guildid, userid, meta_name)
            overwriting = True

        # All macros exist, and we're clear to store
        for macro in macros:
            macro_id = self.__macro_id(guildid, userid, macro)
            query = "INSERT INTO MetaMacros VALUES (%s, %s, %s, %s);"
            self._execute(query, guildid, userid, meta_name, macro_id)

        return overwriting


    def retrieve_macros(self, guildid: int , userid: int, meta_name: str) -> list:
        """
        Retrieve the macro names for a given metamacro.
        Args:
            guildid (int): The Discord ID of the guild where the bot was invoked
            userid (int): The Discord ID of the user invoking the bot
            meta_name (str): The name of the metamacro
        Returns (list): A list of macro names
        """
        query = """
            SELECT Name
            FROM SavedRolls
            RIGHT JOIN MetaMacros
                ON MacroID=macro_id
            WHERE GuildID=%s AND UserID=%s AND MetaName ILIKE %s;
        """
        self._execute(query, guildid, userid, meta_name)
        macros = list(map(lambda item: item[0], self.cursor.fetchall()))

        return macros


    def delete_metamacro(self, guildid: int, userid: int, meta_name: str) -> bool:
        """
        Delete a metamacro from the database.
        Args:
            guildid (int): The Discord ID of the guild where the bot was invoked
            userid (int): The Discord ID of the user invoking the bot
            meta_name (str): The name of the metamacro to delete
        Returns (bool): True if the user had a metamacro by that name on the server
        """
        if not self.__metamacro_exists(guildid, userid, meta_name):
            return False

        query = "DELETE FROM MetaMacros WHERE GuildID=%s AND UserID=%s AND MetaName ILIKE %s;"
        self._execute(query, guildid, userid, meta_name)

        return True


    def metamacro_list(self, guildid: int, userid: int) -> list:
        """
        Retrieve a list of metamacros and their components.
        Args:
            guildid (int): The Discord ID of the guild the bot was invoked in
            userid (int): The Discord ID of the user invoking the bot
        Returns (list): An array of tuples of type (meta_name, associated_macros)
        """
        query = "SELECT DISTINCT MetaName FROM MetaMacros WHERE GuildID=%s AND UserID=%s;"
        self._execute(query, guildid, userid)
        meta_names = list(map(lambda name: name[0], self.cursor.fetchall()))

        records = []
        for meta_name in meta_names:
            macros = self.retrieve_macros(guildid, userid, meta_name)
            meta_name = f"{meta_name}"
            macros = ", ".join(macros)

            records.append((meta_name, macros))

        return records


    def metamacro_count(self, guildid: int, userid: int) -> int:
        """
        Retrieve the number of metamacros the user has in a given guild.
        Args:
            guildid (int): The Discord ID of the guild the bot was invoked in
            userid (int): The Discord ID of the user invoking the bot
        Returns (int): The number of metamacros the user has in this guild
        """
        records = self.metamacro_list(guildid, userid)
        return len(records)


    def __macro_exists(self, guildid: int, userid: int, macro_name: str) -> bool:
        """
        Determine if a given macro exists in SavedRolls.
        Args:
            guildid (int): The Discord ID of the guild the bot was invoked in
            userid (int): The Discord ID of the user invoking the bot
            macro_name (str): The name of the macro
        Returns (bool): True if the macro exists for that user in that guild
        """
        query = "SELECT * FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self._execute(query, guildid, userid, macro_name)
        result = self.cursor.fetchone()

        return result is not None


    def __macro_id(self, guildid: int, userid: int, macro_name: str) -> int:
        """
        Retrieve the macro_id of a given macro.
        Args:
            guildid (int): The Discord ID of the guild the bot was invoked in
            userid (int): The Discord ID of the user invoking the bot
            macro_name (str): The name of the macro in question
        Returns (int): The Discord ID of the given macro
        """
        if not self.__macro_exists(guildid, userid, macro_name):
            raise KeyError(f"Error! {macro_name} doesn't exist!")

        query = "SELECT macro_id FROM SavedROLLS WHERE Guild=%s AND ID=%s AND Name ILIKE %s;"
        self._execute(query, guildid, userid, macro_name)
        result = self.cursor.fetchone()

        return result[0]


    def __metamacro_exists(self, guildid: int, userid: int, metamacro_name: str) -> bool:
        """
        Determine if a given metamacro exists.
        Args:
            guildid (int): The Discord ID of the guild in which the bot was invoked
            userid (int): The Discord ID of the user invoking the bot
        Returns (bool): True if the user has a metamacro by that name in that guild
        """
        query = "SELECT * FROM MetaMacros WHERE GuildID=%s AND UserID=%s AND MetaName ILIKE %s;"
        self._execute(query, guildid, userid, metamacro_name)
        result = self.cursor.fetchone()

        return result is not None
