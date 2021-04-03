"""traditional.py - Performs traditional rolls for the user."""

import discord
import dice

from storyteller import engine # pylint: disable=cyclic-import
from storyteller import roll # pylint: disable=cyclic-import
from .response import Response

async def traditional(ctx, command) -> Response:
    """Perform a traditional roll if appropriate."""
    response = None
    send = __traditional_roll(ctx.author, command)
    if send:
        response = Response(Response.TRADITIONAL)
        if isinstance(send, discord.Embed):
            response.embed = send
        else:
            response.content = send

    return response

def is_valid_traditional(syntax: str) -> bool:
    """Determines whether the syntax is a valid traditional roll."""

    # We just try a full roll, because it's cheaper than using roll.traditional.roll_from_string
    try:
        dice.roll(syntax)
        return True
    except dice.DiceBaseException:
        return False

def __traditional_roll(author, command):
    """A "traditional" roll, such as 5d10+2."""
    compact = command["compact"]
    syntax = command["syntax"]
    comment = command["comment"]
    description = "" # Used to show individual dice

    # Get the rolls and assemble the fields
    result = roll.traditional.roll_from_string(syntax)
    if not result:
        return None

    if result.is_initiative:
        suggestion = "Rolling initiative? Try the /mi command!"
        if comment:
            comment += f"\n{suggestion}"
        else:
            comment = suggestion

    # Show the individual dice if more than 1 were rolled
    if result.equation != result.total:
        description = result.equation

    # Compact mode means no embed
    if compact:
        compact_string = ""
        if description:
            compact_string = f"{description} ="

        compact_string = f"{compact_string} {result.total}"
        if comment:
            compact_string += f"\n> {comment}"

        return compact_string

    # Not using compact mode!
    fields = [("Result", result.total, False),]

    embed = engine.build_embed(
        author=author, header=syntax, color=0x000000, fields=fields,
        footer=comment, description=description
    )

    return embed
