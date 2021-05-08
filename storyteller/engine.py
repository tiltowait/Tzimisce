"""The main Tzimisce dicebot class."""

import re
import asyncio

import discord

from storyteller import parse
from storyteller.databases import RollDB, StatisticsDB

# Suggestion Stuff
suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`")
invokex = re.compile(r"/m(?P<will>w)?(?P<compact>c)?(?P<no_botch>z)? (?P<syntax>.*)")

# Database stuff
database = RollDB()
statistics = StatisticsDB()

async def handle_command(command, ctx, send=True):
    """Parse every message and determine if action is needed."""

    # The COMMAND dict contains info on compact mode, willpower, comment,
    # and the command syntax. At this point, the syntax is unvalidated and
    # may be in error. Validators below determine if syntax is actionable
    # or display an error message.

    # Discord will reject messages that are too long
    if command["comment"] and len(command["comment"]) > 500:
        reduction = len(command["comment"]) - 500
        characters = "character" if reduction == 1 else "characters"

        await ctx.reply(f"Comment too long by {reduction} {characters}.")
        return

    # If the command involves the RollDB, we need to modify the syntax first
    response = await parse.database(ctx, command)
    if isinstance(response, dict): # Database didn't generate a user response
        command = response
        response = None

    # Pooled roll
    if not response:
        response = await parse.pool(ctx, command)

    # Traditional roll (e.g. 2d10+4)
    if not response:
        response = await parse.traditional(ctx, command)

    # Meta-macros
    if not response and command["syntax"][0] == "$":
        response = parse.metamacros(ctx, command, handle_command)
        if isinstance(response, parse.MetaMacro):
            await __run_metamacro(response)
            return

    if response:
        if not send:
            return response
        await __send_response(ctx, response)
        return

    # Unrecognized input
    await ctx.reply("Come again?")

async def __send_response(ctx, response):
    """Sends the response to the given channel."""
    message = None

    # If the ctx's content is None, then there is no message to reply to
    if ctx.message.content is None:
        message = await ctx.send(
            embed=response.embed, content=response.mentioned_content(ctx.author)
        )
    else:
        message = await ctx.reply(embed=response.embed, content=response.content)

    if response.add_reaction:
        await message.add_reaction("👍")

    if ctx.guild:
        statistics.increment_rolls(ctx.guild.id)
        if response.is_traditional:
            statistics.increment_traditional_rolls(ctx.guild.id)


async def __run_metamacro(metamacro):
    """Performs each macro in a MetaMacro until finished."""
    while not metamacro.is_done:
        # Tell the user what macro we're rolling
        macro = metamacro.next_macro_name
        roll_msg = f"Rolling `{macro}` ..."

        response = await metamacro.run_next_macro()
        if response.content:
            response.content = f"{roll_msg}\n\n{response.content}"
        else:
            response.content = roll_msg

        # Send the response and sleep half a second
        await __send_response(metamacro.ctx, response)
        await asyncio.sleep(0.5)


async def show_stored_rolls(ctx):
    """Sends an embed describing all the user's macros."""
    stored_rolls = database.stored_rolls(ctx.guild.id, ctx.author.id)
    meta_records = parse.meta_records(ctx.guild.id, ctx.author.id)

    fields = stored_rolls + meta_records

    if len(stored_rolls) == 0:
        await ctx.reply(f"You have no macros on {ctx.guild}!")
    else:
        embed = build_embed(
            title="Stored Rolls",
            color=0x1F3446,
            fields=fields,
        )
        await ctx.reply("List sent. Please check your DMs!")
        await ctx.author.send(
            content=f"Here are your macros on **{ctx.guild}**:",
            embed=embed
        )

def macro_counts(ctx) -> list:
    """Returns the number of macros and metamacros the user has stored."""
    macro_count = database.macro_count(ctx.guild.id, ctx.author.id)
    meta_count = parse.meta_count(ctx.guild.id, ctx.author.id)

    return (macro_count, meta_count)

async def delete_user_rolls(ctx):
    """Deletes all of a user's macros on the given guild."""
    database.delete_user_rolls(ctx.guild.id, ctx.author.id)
    message = f"Deleted your macros on {ctx.guild}."

    if ctx.message.content:
        await ctx.reply(message)
    else:
        await ctx.send(f"{ctx.author.mention}: {message}")


def help_embed(prefix):
    """Return a handy help embed."""

    # Not using build_embed() because we need a little more than it offers
    embed=discord.Embed(
        title="[Tzimisce] | Help", url="https://tiltowait.github.io/Tzimisce/",
        description="Click above for a complete listing of commands: Macros, initiative, and more!"
    )
    embed.add_field(
        name="Basic Syntax",
        value=f"```{prefix} <pool> [difficulty] [specialty] # comment```Only `pool` is required.",
        inline=False
    )
    embed.add_field(name="Example", value=f"```{prefix} 8 5 Mesmerizing # Summon```", inline=False)
    embed.add_field(
        name="Become a Patron",
        value=r"Support \[Tzimisce\]'s development [here](https://www.patreon.com/tzimisce)!",
        inline=False
    )

    return embed


def build_embed(
    fields, author=None, title="", color=0x1F3446, description="", header=None,
    footer=None
):
    """Return a discord embed with a variable number of fields."""
    # pylint: disable=too-many-arguments

    embed = discord.Embed(
        title=title, colour=discord.Colour(color), description=description
    )

    if footer:
        embed.set_footer(text=footer)

    if author:
        avatar = author.avatar_url
        author = author.display_name

        if header:
            author += f": {header}"

        embed.set_author(name=author, icon_url=avatar)

    for field in fields:
        name = field[0]
        value = field[1]
        inline = False

        if len(field) == 3:
            inline = field[2]

        embed.add_field(name=name, value=value, inline=inline)

    return embed
