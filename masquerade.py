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
    command["will"] = True

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(name="mc")
async def compact_roll(ctx, *args):
    """Perform a roll with compact output."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args
    command["compact"] = True

    await tzimisce.Masquerade.handle_command(command, args, ctx)

@bot.command(name="mcw")
async def compact_willpower_roll(ctx, *args):
    """Perform a Willpower roll with compact output."""
    args = " ".join(args)
    command = defaultdict(lambda: None)
    command["syntax"] = args
    command["will"] = True
    command["compact"] = True

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
