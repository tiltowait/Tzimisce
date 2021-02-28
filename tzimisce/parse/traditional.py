"""traditional.py - Performs traditional rolls for the user."""

import re

import discord
import tzimisce
from tzimisce import roll

__tradx = re.compile(
    r"^(?P<syntax>\d+(d\d+)?(\s*\+\s*(\d+|\d+d\d+))*)$"
)
FAILURE = 0
SUCCESS = 1
SUCCESS_WITH_INIT = 2

async def parse(ctx, command, mentioning) -> int:
    """Perform a traditional roll if appropriate."""
    traditional = __tradx.match(command["syntax"])
    if traditional:
        command.update(traditional.groupdict())
        try:
            init, send = __traditional_roll(ctx.author, command)
            if isinstance(send, discord.Embed):
                if mentioning:
                    await ctx.send(content=ctx.author.mention, embed=send)
                else:
                    await ctx.message.reply(embed=send)
            else:
                await ctx.message.reply(send)

            if init:
                return SUCCESS_WITH_INIT
            return SUCCESS
        except ValueError as error:
            await ctx.message.reply(str(error))

        return FAILURE

def __traditional_roll(author, command):
    """A "traditional" roll, such as 5d10+2."""
    compact = command["compact"]
    syntax = command["syntax"]
    comment = command["comment"]
    description = None # Used to show individual dice results
    suggested = False

    # Get the rolls and assemble the fields
    rolls, rolling_initiative = roll.traditional.roll_from_string(syntax)
    result = str(sum(rolls))

    if rolling_initiative:
        suggestion = "Rolling initiative? Try the /mi command!"
        suggested = True
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

        return f"{compact_string}"

    # Not using compact mode!
    fields = [("Result", result, False),]

    embed = tzimisce.masquerade.build_embed(
        author=author, header=syntax, color=0x000000, fields=fields,
        footer=comment, description=description
    )

    return (suggested, embed)
