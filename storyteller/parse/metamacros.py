"""metamacros.py - Defines an interface for checking metamacro input."""

import re

from discord.ext import tasks

from storyteller.databases import MetaMacroDB
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
        macros = __meta_macros.retrieve_metamacro(guildid, userid, syntax)
        metamacro = MetaMacro(ctx, command, macros, handler)

        return metamacro

    match = __store_meta_macro.match(syntax)
    if match:
        meta_name = match.group("name")
        macros = match.group("macros").split()

        try:
            __meta_macros.store_metamacro(guildid, userid, meta_name, *macros)
            response.content = f"Meta-macro `{meta_name}` saved!"
        except KeyError as err:
            response.content = str(err)

        return response

    match = __delete_meta_macro.match(syntax)
    if match:
        meta_name = match.group("name")
        if __meta_macros.delete_metamacro(guildid, userid, meta_name):
            response.content = f"Deleted meta-macro `{meta_name}`!"
            return response
        response.content = f"Error! You have no meta-macro named `{meta_name}` on this server!"
        return response

    return None

class MetaMacro:
    """Stores a context, command, and list of macros to perform."""

    def __init__(self, ctx, command, macros, handler):
        self.ctx = ctx
        self.command = command
        self.macros = macros
        self.handler = handler

    async def next_macro(self):
        """Performs the next macro in the list."""
        if len(self.macros) == 0:
            return

        macro = self.macros.pop(0)
        self.command["syntax"] = macro
        self.command["comment"] = None
        await self.handler(self.command, self.ctx)

    @property
    def is_done(self):
        """Returns True if the macro list is empty."""
        return len(self.macros) == 0
