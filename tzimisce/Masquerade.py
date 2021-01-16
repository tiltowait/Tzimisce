"""The main Tzimisce dicebot class."""

import re
import random
from collections import defaultdict

import discord
from tzimisce.RollDB import RollDB
from tzimisce.Pool import Pool
from tzimisce import PlainRoll

random.seed()

poolx = re.compile(
    r"^(?P<pool>\d+)\s*(?P<difficulty>\d+)?\s*(?P<auto>\d+)?(?P<specialty> \D[^#]*)?$"
)
tradx = re.compile(
    r"^(?P<syntax>\d+(d\d+)?(\s*\+\s*(\d+|\d+d\d+))*)$"
)

# Suggestion Stuff
suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`")
invokex = re.compile(r"/m(?P<will>w)?(?P<compact>c)? (?P<syntax>.*)")

# Colors help show, at a glance, if a roll was successful
EXCEPTIONAL_COLOR = 0x00FF00
SUCCESS_COLOR = 0x0DC06B
MARGINAL_COLOR = 0x14A1A0
FAIL_COLOR = 0X777777
BOTCH_COLOR = 0XfF0000

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
        characters = "character"
        if reduction > 1: # Because I can't risk improper pluralization
            characters += "s"

        await ctx.message.reply(f"Comment too long by {reduction} {characters}.")
        return

    # If the command involves the RollDB, we need to modify the syntax first
    if command["syntax"][0].isalpha(): # Only macros start with alpha
        query_result = database.query_saved_rolls(
            guild=ctx.guild.id,
            userid=ctx.author.id,
            command=command
        )

        # Created, updated, or deleted a roll (or error)
        if isinstance(query_result, str):
            adding_reaction = False

            if query_result[-2:] == "`?":
                # First, create the invocation
                will = command["will"] or ""
                compact = command["compact"] or ""
                invoke = f"/m{will}{compact}"

                # Next, get the suggestion
                suggestion = suggestx.match(query_result).group("suggestion")

                # Next, substitute it from the original syntax
                split = command["syntax"].split()
                split[0] = suggestion
                new_syntax = " ".join(split)

                # Build the new command
                new_command = f"{invoke} {new_syntax}"

                # Replace!
                query_result = query_result.replace(suggestion, new_command)
                adding_reaction = True

            message = await ctx.message.reply(f"{query_result}")

            if adding_reaction:
                await message.add_reaction("👍")
            return

        # Retrieved a roll
        command = query_result

    # Pooled roll
    pool = poolx.match(command["syntax"])
    if pool:
        command.update(pool.groupdict())
        send = __pool_roll(ctx.author, command)

        if isinstance(send, discord.Embed):
            if mentioning:
                await ctx.send(content=ctx.author.mention, embed=send)
            else:
                await ctx.message.reply(embed=send)
        else: # It's a string
            await ctx.message.reply(send)

        if ctx.guild:
            database.increment_rolls(ctx.guild.id)
        return

    # Traditional roll (e.g. 2d10+4)
    traditional = tradx.match(command["syntax"])
    if traditional:
        command.update(traditional.groupdict())
        try:
            send = __traditional_roll(ctx.author, command)
            if isinstance(send, discord.Embed):
                if mentioning:
                    await ctx.send(content=ctx.author.mention, embed=send)
                else:
                    await ctx.message.reply(embed=send)
            else:
                await ctx.message.reply(send)

            database.increment_rolls(ctx.guild.id)
        except ValueError as error:
            await ctx.message.reply(str(error))

        return

    await ctx.message.reply("Come again?")

async def show_stored_rolls(ctx):
    """Sends an embed describing all the user's macros."""
    stored_rolls = database.stored_rolls(ctx.guild.id, ctx.author.id)
    if len(stored_rolls) == 0:
        await ctx.message.reply("You have no stored rolls!")
    else:
        embed = __build_embed(
            author=ctx.author,
            title="Stored Rolls",
            color=0x1F3446,
            fields=stored_rolls,
        )
        await ctx.message.reply("DM sent!")
        await ctx.author.send(
            content=f"Here are your stored rolls on {ctx.guild}:",
            embed=embed
        )

async def delete_user_rolls(ctx):
    """Deletes all of a user's macros on the given guild."""
    database.delete_user_rolls(ctx.guild.id, ctx.author.id)
    await ctx.message.reply("Deleted all stored rolls.")

def __pool_roll(author, command):
    """
    A pool-based VtM roll. Returns the results in a pretty embed.
    Does not check that difficulty is 1 or > 10.
    """
    will = command["will"]
    compact = command["compact"]
    pool = int(command["pool"])

    if pool < 1:
        return "Pool cannot be lower than 1."

    if pool > 100:
        return "Error! Pools cannot be larger than 100."

    # Difficulty must be between 2 and 10. If it isn't supplied, go with
    # the default value of 6.
    difficulty = command["difficulty"]
    if not difficulty:
        difficulty = 6
    else:
        difficulty = int(difficulty)
        if difficulty > 10:
            difficulty = 10
        elif difficulty < 2:
            difficulty = 2

    # Title format: 'Pool X, difficulty Y'
    title = f"Pool {pool}, diff. {difficulty}"

    # Sometimes, a roll may have auto-successes that can be canceled by 1s.
    autos = command["auto"]
    if autos:
        autos = int(autos)
        title += f", +{pluralize_autos(autos)}"
    else:
        autos = 0

    specialty = command["specialty"] # Doubles 10s if set

    # Perform rolls, format them, and figure out how many successes we have
    results = Pool()
    results.roll(pool, difficulty, will, specialty is not None, autos)

    comment = command["comment"]

    # Compact formatting
    if compact:
        results_string = results.formatted_count()

        compact_string = f"{results.formatted} = **{results_string}**"
        if comment:
            compact_string += f"\n> {comment}"

        if specialty:
            compact_string += f"\n> ***{specialty}***"

        return f"{compact_string}"

    # If not compact, put the results into an embed

    # The embed's color indicates if the roll succeeded, failed, or botched
    color = 0
    if results.successes >= 5:
        color = EXCEPTIONAL_COLOR
    elif results.successes >= 3:
        color = SUCCESS_COLOR
    elif results.successes > 0:
        color = MARGINAL_COLOR
    elif results.successes < 0:
        color = BOTCH_COLOR
    else:
        color = FAIL_COLOR

    # Set up the embed fields
    fields = [("Dice", results.formatted, True)]

    if specialty:
        fields.append(("Specialty", specialty, True))

    fields.append(("Result", results.formatted_count(), False))

    return __build_embed(
        author=author, header=title, color=color, fields=fields,
        footer=comment
    )

def __traditional_roll(author, command):
    """A "traditional" roll, such as 5d10+2."""
    compact = command["compact"]
    syntax = command["syntax"]
    comment = command["comment"]
    description = None # Used to show individual dice results

    # Get the rolls and assemble the fields
    rolls = PlainRoll.roll_string(syntax)
    result = str(sum(rolls))

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

    embed = __build_embed(
        author=author, header=syntax, color=0x000000, fields=fields,
        footer=comment, description=description
    )

    return embed

def help():
    """Return a handy help embed."""
    embed=discord.Embed(title="[Tzimisce] | Help", url="https://tiltowait.github.io/Tzimisce/", description="Click above for a complete listing of commands, including macros (roll saving) and more.")
    embed.add_field(name="Basic Syntax", value="```/m <pool> [difficulty] [specialty] # comment```Difficulty, specialty, and comment are all optional.", inline=False)
    embed.add_field(name="Example", value="```/m 8 7 Domineering # Command```", inline=False)

    return embed

def __build_embed(
    fields, author=None, title="", color=0x1F3446, description="", header=None,
    footer=None
):
    """Return a discord embed with a variable number of fields."""
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

def pluralize_autos(autos):
    """Pluralize 'N auto(s)' as needed"""
    string = f"{autos} auto"
    if autos > 1:
        string += "s"

    return string
