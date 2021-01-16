"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict

import discord
from discord.ext import commands

import tzimisce

bot = commands.Bot(command_prefix="/")

# Commands

@bot.group(invoke_without_command=True, aliases=["m", "mw", "mc", "mcw", "mwc"])
async def standard_roll(ctx, *, args=None):
    """Perform a roll without Willpower."""
    if not args:
        await __help(ctx)
        return

    raw_split = ctx.message.content.split(' ', 1)
    clean_split = ctx.message.clean_content.split(' ', 1)

    if len(raw_split) == 1:
        return

    syntax, comment = split_comment(raw_split[1], clean_split[1])

    command = defaultdict(lambda: None)
    command["syntax"] = syntax.strip()
    command["comment"] = comment.strip() if comment else None

    # See what options the user has selected, if any
    if "w" in ctx.invoked_with:
        command["will"] = "w"
    if "c" in ctx.invoked_with:
        command["compact"] = "c"

    await tzimisce.Masquerade.handle_command(command, ctx)

@bot.command(name="mi")
async def initiative(ctx, arg):
    """Roll a 1d10+arg."""
    try:
        mod = int(arg)
        die = tzimisce.PlainRoll.roll_dice(1, 10)[0]
        init = die + mod

        await ctx.message.reply(f"*{die} + {mod}:*   **{init}**")
    except ValueError:
        await ctx.message.reply("Please supply a positive number!")

# Subcommands

@standard_roll.command(aliases=["coin", "flip", "coinflip",])
async def coin_flip(ctx):
    """Performs a simple coinflip."""
    coin = tzimisce.PlainRoll.roll_dice(1, 2)
    if coin == 1:
        coin = "Heads!"
    else:
        coin = "Tails!"

    await ctx.message.reply(f"{coin}")

@standard_roll.command(name="help")
async def __help(ctx):
    """Displays the basic syntax and a link to the full help file."""
    embed = tzimisce.Masquerade.help()
    await ctx.message.reply(embed=embed)


# Macro-Related. Must be done in a guild.

@standard_roll.command(name="$")
@commands.guild_only()
async def show_stored_rolls(ctx):
    """Displays the user's stored rolls."""
    await tzimisce.Masquerade.show_stored_rolls(ctx)

@standard_roll.command(name="$delete-all")
@commands.guild_only()
async def delete_all(ctx):
    """Deletes all of a user's stored rolls."""
    await tzimisce.Masquerade.delete_user_rolls(ctx)

# Events

def suggestion_to_roll(reaction, user):
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
    suggestion = suggestion_to_roll(reaction, user)
    if suggestion:
        command = defaultdict(lambda: None)
        match = tzimisce.Masquerade.invokex.match(suggestion)
        command.update(match.groupdict())

        ctx = await bot.get_context(reaction.message)
        ctx.author = user # Otherwise, the user is the bot
        await tzimisce.Masquerade.handle_command(command, ctx, True)

        # Remove the old reactions
        await reaction.message.add_reaction("✅")

@bot.event
async def on_ready():
    """Print a message letting us know the bot logged in to Discord."""
    print(f"Logged on as {bot.user}!")
    print(f"Playing on {len(bot.guilds)} servers.")
    print(discord.version_info)

    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_join(guild):
    """When joining a guild, log it for statistics purposes."""
    print(f"Joining {guild}!")
    tzimisce.Masquerade.database.add_guild(guild.id, guild.name)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_remove(guild):
    """We don't want to keep track of guilds we no longer belong to."""
    print(f"Removing {guild}.")
    tzimisce.Masquerade.database.remove_guild(guild.id)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_update(_, after):
    """Sometimes guilds are renamed. Fix that."""
    tzimisce.Masquerade.database.rename_guild(after.id, after.name)

@bot.event
async def on_command_error(ctx, error):
    """Ignore CommandNotFound errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, discord.errors.Forbidden):
        await ctx.message.reply("Permissions error. Please make sure I'm allowed to embed links!")
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Sorry, you can't store macros in private DMs!")
        return
    raise error

# Misc

def __status_message():
    """Sets the bot's Discord presence message."""
    servers = len(bot.guilds)
    return f"/m help | {servers} chronicles"

def split_comment(raw: str, clean: str) -> list:
    """Tries to use the clean user input for a command."""
    try:
        raw_comment = raw.index('#')
        clean_comment = clean.index('#')

        split_candidate = ''

        # A comment, user, or channel tag looks something like <!@2234255345> in
        # the background, which is the input the bot receives. If the user did
        # not use such a tag before their comment, we can trivially sub in the
        # clean text and make things prettier.

        if raw_comment == clean_comment:
            split_candidate = clean
        else:
            split_candidate = raw

        return split_candidate.split('#', 1)
    except ValueError:
        return (raw, None)


bot.run(os.environ["TZIMISCE_TOKEN"])
