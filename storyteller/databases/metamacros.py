"""Defines a Database class for managing metamacros."""

from collections import namedtuple

from .base import Database

class MetaMacroDB(Database):
    """A database manager for handling metamacros."""

    def __init__(self):
        super().__init__()

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

    def retrieve_metamacro(self, guildid, userid, meta_name) -> list:
        """Retrieves the macro names for a given MetaMacro."""
        query = "SELECT MacroID FROM MetaMacros WHERE GuildID=%s AND UserID=%s AND MetaName=%s;"
        self._execute(query, (guildid, userid, meta_name,))
        macro_ids = self.cursor.fetchall()

        # Convert each MacroID to a macro name
        macros = []
        for macro_id in macro_ids:
            macro = self.__macro_name(guildid, userid, macro_id)
            macros.append(macro)

        return macros

    def store_metamacro(self, guildid, userid, meta_name, *macros) -> bool:
        """Stores a metamacro. Raises KeyError if one of the given macros doesn't exist."""
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
            self._execute(query, (guildid, userid, meta_name, macro_id))

        return overwriting


    def delete_metamacro(self, guildid, userid, meta_name) -> bool:
        """Deletes a metamacro from the database."""
        if not self.__metamacro_exists(guildid, userid, meta_name):
            return False

        query = "DELETE FROM MetaMacros WHERE GuildID=%s AND UserID=%s AND MetaName=%s;"
        self._execute(query, (guildid, userid, meta_name,))

        return True

    def metamacro_list(self, guildid, userid) -> list:
        """Returns a list of metamacros and their components."""
        query = "SELECT DISTINCT MetaName FROM MetaMacros WHERE GuildID=%s AND UserID=%s;"
        self._execute(query, (guildid, userid,))
        meta_names = list(map(lambda name: name[0], self.cursor.fetchall()))

        records = []
        for meta_name in meta_names:
            macros = self.__metamacro_composition(guildid, userid, meta_name)
            meta_name = f"Meta: ${meta_name}"
            macros = ", ".join(macros)

            records.append((meta_name, macros))

        return records

    def __metamacro_composition(self, guildid, userid, meta_name) -> list:
        """Returns the list of macros comprising a given metamacro."""
        query = """
            SELECT Name
            FROM SavedRolls
            RIGHT JOIN MetaMacros
                ON MacroID=macro_id
            WHERE GuildID=%s AND UserID=%s AND MetaName=%s;
        """
        self._execute(query, (guildid, userid, meta_name,))
        macros = list(map(lambda item: item[0], self.cursor.fetchall()))

        return macros


    def __macro_exists(self, guildid, userid, macro_name) -> bool:
        """Returns true if a given macro exists in SavedRolls."""
        query = "SELECT * FROM SavedRolls WHERE Guild=%s AND ID=%s AND Name=%s;"
        self._execute(query, (guildid, userid, macro_name,))
        result = self.cursor.fetchone()

        return result is not None


    def __macro_id(self, guildid, userid, macro_name) -> int:
        """Returns the macro_id of a given macro."""
        if not self.__macro_exists(guildid, userid, macro_name):
            raise KeyError(f"Error! {macro_name} doesn't exist!")

        query = "SELECT macro_id FROM SavedROLLS WHERE Guild=%s AND ID=%s AND Name=%s;"
        self._execute(query, (guildid, userid, macro_name,))
        result = self.cursor.fetchone()

        return result[0]


    def __macro_name(self, guildid, userid, macro_id) -> str:
        """Returns the name of a macro, given its ID."""
        query = "SELECT Name FROM SavedRolls WHERE Guild=%s AND ID=%s AND macro_id=%s;"
        self._execute(query, (guildid, userid, macro_id,))
        result = self.cursor.fetchone()

        return result[0]


    def __metamacro_exists(self, guildid, userid, metamacro_name) -> bool:
        """Returns true if a given metamacro exists."""
        query = "SELECT * FROM MetaMacros WHERE GuildID=%s AND UserID=%s AND MetaName=%s;"
        self._execute(query, (guildid, userid, metamacro_name,))
        result = self.cursor.fetchone()

        return result is not None
