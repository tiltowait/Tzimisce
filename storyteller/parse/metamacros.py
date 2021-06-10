"""metamacros.py - Defines an interface for checking metamacro input."""

import re

from storyteller.databases import MetaMacroDB # pylint: disable=cyclic-import
from .response import Response


__meta_macros = MetaMacroDB()

__use_meta_macro = re.compile(r"^\w[\w-]*$")
__store_meta_macro = re.compile(r"^(?P<name>\w[\w-]*)\s*=\s*(?P<macros>.+)$")
__delete_meta_macro = re.compile(r"^(?P<name>\w[\w-]*)\s*=\s*$")


def parse(ctx, command, handler):
    """Performs, deletes, or creates a metamacro."""
    if not ctx.guild:
        return "Sorry, you can't use mata-macros in a private message!"

    guildid = ctx.guild.id
    userid = ctx.author.id
    syntax = command["syntax"][1:] # Remove preceding '$'
    response = Response(Response.META_MACRO)

    # See if using a metamacro
    if __use_meta_macro.match(syntax):
        macros = __meta_macros.retrieve_macros(guildid, userid, syntax)
        if macros:
            return MetaMacro(ctx, command, macros, handler)
        response.content = f"Error! You have no meta-macro named `${syntax}`."
        return response

    match = __store_meta_macro.match(syntax)
    if match:
        meta_name = match.group("name")
        macros = match.group("macros").split()

        if not 2 <= len(macros) <= 10:
            response.content = "Error! Meta-macros must contain between 2-10 macros."
        else:
            try:
                overwriting = __meta_macros.store_metamacro(guildid, userid, meta_name, *macros)
                if overwriting:
                    response.content = f"Meta-macro `${meta_name}` updated!"
                else:
                    response.content = f"Meta-macro `${meta_name}` created!"
            except KeyError as err:
                response.content = str(err)

        return response

    match = __delete_meta_macro.match(syntax)
    if match:
        meta_name = match.group("name")
        if __meta_macros.delete_metamacro(guildid, userid, meta_name):
            response.content = f"Deleted meta-macro `${meta_name}`!"
            return response
        response.content = f"Error! You have no meta-macro named `${meta_name}` on this server!"
        return response

    return None


def meta_records(guildid, userid):
    """Returns the MetaRecords for the user."""
    return __meta_macros.metamacro_list(guildid, userid)


def meta_count(guildid, userid):
    """Returns the number of MetaMacros for the user."""
    return __meta_macros.metamacro_count(guildid, userid)


class MetaMacro:
    """Stores a context, command, and list of macros to perform."""

    def __init__(self, ctx, command, macros, handler):
        self.ctx = ctx
        self.command = command
        self.macros = macros
        self.handler = handler


    async def run_next_macro(self):
        """Performs the next macro in the list."""
        if len(self.macros) == 0:
            return

        macro = self.macros.pop(0)
        self.command["syntax"] = macro
        self.command["comment"] = None
        return await self.handler(self.command, self.ctx, send=False)


    @property
    def is_done(self):
        """Returns True if the macro list is empty."""
        return len(self.macros) == 0


    @property
    def next_macro_name(self):
        """Returns the name of the next macro to be run."""
        try:
            return self.macros[0]
        except IndexError:
            return None
