"""metamacros.py - Defines an interface for checking metamacro input."""

# Metamacros are macros that call other macros. They can be particularly useful
# for players who have a "daily routine", such as a Tremere who casts a number
# of rituals each night. They require at least three or more macros in their
# composition, but those macros need not be unique.

import re
from typing import Union

from storyteller.databases import MetaMacroDB # pylint: disable=cyclic-import
from .response import Response
from .metamacro_class import MetaMacro


__metamacros = MetaMacroDB()

__using_metamacro = re.compile(r"^\w[\w-]*$")
__creating_metamacro = re.compile(r"^(?P<name>\w[\w-]*)\s*=\s*(?P<macros>.+)$")
__deleting_metamacro = re.compile(r"^(?P<name>\w[\w-]*)\s*=\s*$")


def parse(ctx, command: dict, handler) -> Union[Response, MetaMacro]:
    """
    Parse metamacro input, allowing for creation, deletion, and retrieval but
    only the most limited of updating.
    Args:
        ctx (discord.extensions.Context): The bot context for the command
        command (dict): The user's input, server settings, and similar info
        handler (function): A completion handler used by the Metamacro class to
                            perform its macros
    Returns (Union[Response, MetaMacro]): A Response object to show the user
    """
    response = Response(Response.META_MACRO)
    response.ephemeral = True

    if not ctx.guild:
        response.content = "Sorry, you can't use mata-macros in a private message!"
        return response

    guildid = ctx.guild.id
    userid = ctx.author.id
    syntax = command["syntax"][1:] # Remove preceding '$' that all metamacros have

    # We follow a similar workflow to RollDB: Check the user syntax against a
    # variety of patterns, only stopping when we get a match and sending back
    # an error if they gave a bad command

    if __using_metamacro.match(syntax):
        macros = __metamacros.retrieve_macros(guildid, userid, syntax)
        if macros:
            return MetaMacro(ctx, command, macros, handler)
        response.content = f"Error! You have no meta-macro named `${syntax}`."
        return response

    # Metamacro creation is similar to macro creation:
    # /m $metamacro = macro1 macro2 ... macroN
    match = __creating_metamacro.match(syntax)
    if match:
        meta_name = match.group("name")
        macros = match.group("macros").split()

        if not 2 <= len(macros) <= 10:
            response.content = "Error! Meta-macros must contain between 2-10 macros."
        else:
            try:
                overwriting = __metamacros.store_metamacro(guildid, userid, meta_name, *macros)
                if overwriting:
                    response.content = f"Meta-macro `${meta_name}` updated!"
                else:
                    response.content = f"Meta-macro `${meta_name}` created!"
            except KeyError as err:
                response.content = str(err)

        return response

    # Like creation, metamacro deletion is similar to regular macros:
    # /m $metamacro =
    match = __deleting_metamacro.match(syntax)
    if match:
        meta_name = match.group("name")
        if __metamacros.delete_metamacro(guildid, userid, meta_name):
            response.content = f"Deleted meta-macro `${meta_name}`!"
        else:
            response.content = f"Error! You have no meta-macro named `${meta_name}` on this server!"

        return response

    # The user gave a bad metamacro command, so send back no response
    return None


def meta_records(guildid: int, userid: int) -> list[tuple[str, list[str]]]:
    """
    Retrieve the "meta-records" for the user. This function is effectively a
    wrapper for the MetaMacroDB class's metamacro_list() method.
    Args:
        guildid (int): The Discord ID of the guild the user is invoking from
        userid (int): The Discord ID of the user requesting the list
    Returns (list): A list of meta-records
    """

    # A meta-record is a tuple with a string (metamacro name) as the first element
    # and a list of strings (associated macro names) as the second. In the future,
    # this may be changed to a namedtuple for the sake of clarity.

    return __metamacros.metamacro_list(guildid, userid)


def meta_count(guildid: int, userid: int) -> int:
    """
    Retrieve the number of metamacros the user has in a given guild. This
    function is a wrapper for the MetaMacroDB metamacro_count() method.
    Args:
        guildid (int): The Discord ID of the guild in question
        userid (int): The Discord ID of the user
    Returns (int): The number of metamacros the user has in the guild
    """
    return __metamacros.metamacro_count(guildid, userid)
