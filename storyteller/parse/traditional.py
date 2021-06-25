"""traditional.py - Performs traditional rolls for the user."""

from typing import Optional, Union

import discord
import dice

from storyteller import engine # pylint: disable=cyclic-import
from storyteller import roll # pylint: disable=cyclic-import
from .response import Response


async def traditional(ctx, command: dict) -> Optional[Response]:
    """
    Parse user input to determine if they are performing a "traditional" roll.
    If they are, roll it and return the results.
    Args:
        ctx (discord.ext.commands.Context): The bot invocation context
        command (dict): The user's syntax, comment, invocation parameters, and
                        server settings
    """
    result = __traditional_roll(ctx.author, command)
    if result:
        if isinstance(result, discord.Embed):
            return Response(Response.TRADITIONAL, embed=result)

        return Response(Response.TRADITIONAL, content=result)


def is_valid_traditional(syntax: str) -> bool:
    """
    Determine whether the syntax is a valid traditional roll.
    Args:
        syntax (str): The user's command syntax
    Returns (bool): True if the syntax is vaild for a traditional roll
    """

    # We just try a full roll, because it's cheaper than using roll.traditional.roll_from_string()
    try:
        dice.roll(syntax)
        return True
    except dice.DiceBaseException:
        return False


def __traditional_roll(author, command: dict) -> Union[str, discord.Embed]:
    """
    Perform a "traditional" roll, such as 5d10+2.
    Args:
        author: The Discord user who invoked the bot
        command (dict): The user's syntax, comment, invocation parameters, and
                        server settings
    Returns (Union[str, discord.Embed]): The formatted results of the user's roll
    """
    compact = command["use_compact"]
    syntax = command["syntax"]
    comment = command["comment"]
    description = "" # Used for showing individual dice if there are more than one

    # Get the rolls and assemble the fields
    result = roll.traditional.roll_from_string(syntax)
    if not result:
        return None

    # Suggest the initiative manager if it looks like they're rolling initiative
    if result.is_initiative:
        suggestion = "Rolling initiative? Try the /mi command!"
        if comment:
            comment += f"\n{suggestion}"
        else:
            comment = suggestion

    # Show the individual dice if more than one were rolled
    if result.equation != result.total:
        description = result.equation

    # RESULT GENERATION

    if compact:
        # The user or server has selected compact mode instead of Discord embeds
        compact_string = ""
        if description:
            compact_string = f"{description} ="

        compact_string = f"{compact_string} {result.total}"
        if comment:
            compact_string += f"\n> {comment}"

        return compact_string

    # Not using compact mode! Build the embed

    fields = [("Result", result.total, False),]

    embed = engine.build_embed(
        author=author, header=syntax, color=0x000000, fields=fields,
        footer=comment, description=description
    )

    return embed
