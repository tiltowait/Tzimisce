"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict

import discord
from discord.ext import commands

import tzimisce

bot = commands.Bot(command_prefix="/")

# Commands

@bot.command(name="m")
async def standard_roll(ctx, *args):
    """Perform a roll without Willpower."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(name="mw")
async def willpower_roll(ctx, *args):
    """Perform a roll with Willpower."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args
    command["will"] = "w"

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(name="mc")
async def compact_roll(ctx, *args):
    """Perform a roll with compact output."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args
    command["compact"] = "c"

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(aliases=["mcw", "mwc",])
async def compact_willpower_roll(ctx, *args):
    """Perform a Willpower roll with compact output."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args
    command["will"] = "w"
    command["compact"] = "c"

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(name="mi")
async def initiative(ctx, arg):
    """Roll a 1d10+arg."""
    try:
        mod = int(arg)
        die = tzimisce.PlainRoll.roll_dice(1, 10)[0]
        init = die + mod

        await ctx.send(f"{ctx.author.mention}: *{die} + {mod}:*   **{init}**")
    except ValueError:
        await ctx.send(f"{ctx.author.mention}: Please supply a positive number!")

# Events

def should_roll_suggestion(reaction, user):
    """Returns a suggested macro if the correct user replies with a thumbsup."""
    message = reaction.message
    if reaction.emoji == "👍" and message.author == bot.user:
        # Don't allow rolling it more than once
        for react in message.reactions:
            if react.emoji == "✅":
                return None

        if not message.embeds and user in message.mentions:
            match = tzimisce.Masquerade.suggestx.search(message.content)
            if match:
                return match.group("suggestion")

    return None

@bot.event
async def on_reaction_add(reaction, user):
    """Rolls a macro correction suggestion if certain conditions are met."""
    suggestion = should_roll_suggestion(reaction, user)
    if suggestion:
        command = defaultdict(lambda: None)
        match = tzimisce.Masquerade.invokex.match(suggestion)
        command.update(match.groupdict())

        ctx = await bot.get_context(reaction.message)
        ctx.author = user # Otherwise, the user is the bot
        await tzimisce.Masquerade.handle_command(command, match["syntax"], ctx)

        # Remove the old reactions
        await reaction.message.add_reaction("✅")

@bot.event
async def on_ready():
    """Print a message letting us know the bot logged in to Discord."""
    print(f"Logged on as {bot.user}!")

    guilds = len(bot.guilds)
    print(f"Playing on {guilds} servers.")
    print(discord.version_info)

    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_join(guild):
    """When joining a guild, log it for statistics purposes."""
    print(f"Joining {guild}")
    tzimisce.Masquerade.database.add_guild(guild.id, guild.name)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_remove(guild):
    """We don't want to keep track of guilds we no longer belong to."""
    print(f"Removing {guild}")
    tzimisce.Masquerade.database.remove_guild(guild.id)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_update(before, after):
    """Sometimes guilds are renamed. Fix that."""
    tzimisce.Masquerade.database.rename_guild(after.id, after.name)

@bot.event
async def on_command_error(ctx, error):
    """Ignore CommandNotFound errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

# Misc

def __status_message():
    """Sets the bot's Discord presence message."""
    servers = len(bot.guilds)
    return f"/m help | {servers} chronicles"

bot.run(os.environ["TZIMISCE_TOKEN"])
