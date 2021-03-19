"""traditional.py - Performs traditional rolls for the user."""

import re

import discord
from storyteller import engine # pylint: disable=cyclic-import
from storyteller import roll # pylint: disable=cyclic-import
from .response import Response

__tradx = re.compile(
    r"^(?P<syntax>\d+(d\d+)?(\s*\+\s*(\d+|\d+d\d+))*)$"
)

async def parse(ctx, command, mentioning) -> Response:
    """Perform a traditional roll if appropriate."""
    traditional = __tradx.match(command["syntax"])
    response = None
    if traditional:
        command.update(traditional.groupdict())

        send = __traditional_roll(ctx.author, command)
        response = Response(Response.TRADITIONAL)
        if isinstance(send, discord.Embed):
            response.embed = send
            if mentioning:
                response.content = ctx.author.mention
        else:
            response.content = send

    return response

def __traditional_roll(author, command):
    """A "traditional" roll, such as 5d10+2."""
    compact = command["compact"]
    syntax = command["syntax"]
    comment = command["comment"]
    description = None # Used to show individual dice

    # Get the rolls and assemble the fields
    rolls, rolling_initiative = roll.traditional.roll_from_string(syntax)
    result = str(sum(rolls))

    if rolling_initiative:
        suggestion = "Rolling initiative? Try the /mi command!"
        if comment:
            comment += f"\n{suggestion}"
        else:
            comment = suggestion

    # Show the individual dice if more than 1 were rolled
    if len(rolls) > 1:
        description = "+".join([str(roll) for roll in rolls])

    # Compact mode means no embed
    if compact:
        compact_string = ""
        if description:
            compact_string = f"{description} ="

        compact_string = f"{compact_string} {result}"
        if comment:
            compact_string += f"\n> {comment}"

        return compact_string

    # Not using compact mode!
    fields = [("Result", result, False),]

    embed = engine.build_embed(
        author=author, header=syntax, color=0x000000, fields=fields,
        footer=comment, description=description
    )

    return embed
