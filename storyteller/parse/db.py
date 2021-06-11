"""db.py - Determine whether the user is invoking the macro database."""

# In the future, this module should be refactored to handle most of the RollDB's
# heavy lifting. In particular, it should handle any and all modifications to
# macro values (i.e. /m hunt +2), as the database shouldn't care about how the
# underlying data is used after it's been fetched. As part of that effort, this
# module should be renamed to something like "macro_parse" or similar, as it
# does not handle parsing duties for all of the bot's databases.
#
# See also: the discussion section in databases/database.py.

import re
from typing import Union

import discord

# This import might be avoided by passing the RollDB as an argument
from storyteller import engine # pylint: disable=cyclic-import
from storyteller.parse.response import Response

__suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`") # Checks if a string's a bot macro suggestion


async def database(ctx, command: dict) -> Union[dict, Response]:
    """
    Parse commands invoking the macro database.
    Args:
        command (dict): The dictionary describing the user's command
    Returns (Union[dict, Response]): The original command if not a database query or an error
                                     Response to send to the user.
    """
    query_result = None

    # If the command syntax doesn't start with an alpha character, then the user
    # isn't doing anything with the macro database, and we simply return the
    # unmodified command for futher processing
    if command["syntax"][0].isalpha():
        if ctx.channel.type is discord.ChannelType.private:
            response = Response(Response.DATABASE)
            response.content = "Sorry, you can't store macros in private DMs!"
            return response

        # This is either a modified command (in the case of a successful
        # database hit) or an error message. If the former, pass that along for
        # further processing; if the latter, wrap it up in a Response object to
        # present to the user
        query_result = engine.database.query_saved_rolls(
            guild=ctx.guild.id,
            userid=ctx.author.id,
            command=command
        )

        # Created, updated, or deleted a roll (or error)
        if isinstance(query_result, str):
            response = Response(Response.DATABASE)

            # Database offered macro suggestion
            if query_result[-2:] == "`?":
                # First, determine the invocation options
                will = command["will"] or ""
                compact = command["use_compact"] or ""
                no_botch = command["never_botch"] or ""

                invocation = f"/m{will}{compact}{no_botch}"

                suggestion = __suggestx.match(query_result).group("suggestion")

                # Next, replace the incorrect macro name with the suggestion
                split = command["syntax"].split()
                split[0] = suggestion
                new_syntax = " ".join(split)

                # Build the new command
                new_command = f"{invocation} {new_syntax}"

                # Replace!
                query_result = new_command.join(query_result.rsplit(suggestion, 1))
                response.add_reaction = True

            response.content = query_result

            return response

    return query_result or command
