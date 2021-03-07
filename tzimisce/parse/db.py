"""db.py - Determine whether the user is invoking the macro database."""

import re
import discord

from tzimisce import masquerade # pylint: disable=cyclic-import
from tzimisce.parse.response import Response

__suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`")

async def parse(ctx, command):
    """Inspects command for database queries and acts on them as necessary."""
    query_result = None

    if command["syntax"][0].isalpha(): # Only macros start with alpha
        if ctx.channel.type is discord.ChannelType.private:
            response = Response(Response.DATABASE)
            response.content = "Sorry, you can't store macros in private DMs!"
            return response

        query_result = masquerade.database.query_saved_rolls(
            guild=ctx.guild.id,
            userid=ctx.author.id,
            command=command
        )

        # Created, updated, or deleted a roll (or error)
        if isinstance(query_result, str):
            response = Response(Response.DATABASE)

            # Database offered macro suggestion
            if query_result[-2:] == "`?":
                # First, create the invocation
                will = command["will"] or ""
                compact = command["compact"] or ""
                no_botch = command["no_botch"] or ""
                invoke = f"/m{will}{compact}{no_botch}"

                # Next, get the suggestion
                suggestion = __suggestx.match(query_result).group("suggestion")

                # Next, substitute it from the original syntax
                split = command["syntax"].split()
                split[0] = suggestion
                new_syntax = " ".join(split)

                # Build the new command
                new_command = f"{invoke} {new_syntax}"

                # Replace!
                query_result = query_result.replace(suggestion, new_command)
                response.add_reaction = True

            response.content = query_result

            return response

    return query_result or command
