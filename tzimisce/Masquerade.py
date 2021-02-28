"""The main Tzimisce dicebot class."""

import re
import random

import discord
from tzimisce.database import RollDB
from tzimisce import parse

random.seed()

# Suggestion Stuff
suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`")
invokex = re.compile(r"/m(?P<will>w)?(?P<compact>c)? (?P<syntax>.*)")

# Database stuff
database = RollDB()

async def handle_command(command, ctx, mentioning=False):
    """Parse every message and determine if action is needed."""

    # The COMMAND dict contains info on compact mode, willpower, comment,
    # and the command syntax. At this poitn, the syntax is unvalidated and
    # may be in error. Validators below determine if syntax is actionable
    # or display an error message.

    # Discord will reject messages that are too long
    if command["comment"] and len(command["comment"]) > 500:
        reduction = len(command["comment"]) - 500
        characters = "character" if reduction == 1 else "characters"

        await ctx.message.reply(f"Comment too long by {reduction} {characters}.")
        return

    # If the command involves the RollDB, we need to modify the syntax first
    command = await parse.db.parse(ctx, command)

    # Pooled roll
    response = await parse.pool.parse(ctx, command, mentioning)
    if response:
        if mentioning:
            await ctx.send(embed=response.embed, content=response.content)
        else:
            await ctx.message.reply(embed=response.embed, content=response.content)

        if ctx.guild:
            database.increment_rolls(ctx.guild.id)
        return

    # Traditional roll (e.g. 2d10+4)
    response = await parse.traditional.parse(ctx, command, mentioning)
    if response:
        if mentioning:
            await ctx.send(embed=response.embed, content=response.content)
        else:
            await ctx.message.reply(embed=response.embed, content=response.content)

        if ctx.guild:
            database.increment_rolls(ctx.guild.id)
            database.increment_traditional_rolls(ctx.guild.id)

            # Initiative was suggested
            if response.init_suggested:
                database.suggested_initiative(ctx.guild.id)
        return

    # Unrecognized input
    await ctx.message.reply("Come again?")

async def show_stored_rolls(ctx):
    """Sends an embed describing all the user's macros."""
    stored_rolls = database.stored_rolls(ctx.guild.id, ctx.author.id)
    if len(stored_rolls) == 0:
        await ctx.message.reply(f"You have no macros on {ctx.guild}!")
    else:
        embed = build_embed(
            title="Stored Rolls",
            color=0x1F3446,
            fields=stored_rolls,
        )
        await ctx.message.reply("List sent. Please check your DMs!")
        await ctx.author.send(
            content=f"Here are your macros on {ctx.guild}:",
            embed=embed
        )

async def delete_user_rolls(ctx):
    """Deletes all of a user's macros on the given guild."""
    database.delete_user_rolls(ctx.guild.id, ctx.author.id)
    await ctx.message.reply(f"Deleted your macros on {ctx.guild}.")

def help_embed(prefix):
    """Return a handy help embed."""

    # Not using build_embed() because we need a little more than it offers
    embed=discord.Embed(
        title="[Tzimisce] | Help", url="https://tiltowait.github.io/Tzimisce/",
        description="Click above for a complete listing of commands: Macros, initiative, and more!"
    )
    embed.add_field(
        name="Basic Syntax",
        value=f"```{prefix}m <pool> [difficulty] [specialty] # comment```Only `pool` is required.",
        inline=False
    )
    embed.add_field(name="Example", value=f"```{prefix}m 8 5 Mesmerizing # Summon```", inline=False)

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
