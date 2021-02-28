"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict
import argparse

import discord
from discord.ext import commands

import tzimisce
from tzimisce.initiative import InitiativeManager

# Setup

# This is a defaultdict, lambda None
CUSTOM_PREFIXES = tzimisce.masquerade.database.get_all_prefixes()

async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return __get_prefix(message.guild)

bot = commands.Bot(command_prefix=determine_prefix)
bot.remove_command("help")

# Commands

@bot.group(invoke_without_command=True, name="m", aliases=["mw", "mc", "mcw", "mwc"])
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

    if len(syntax) == 0: # Can happen if user supplies a comment without syntax
        raise IndexError

    command = defaultdict(lambda: None)
    command["syntax"] = syntax.strip()
    command["comment"] = comment.strip() if comment else None

    # See what options the user has selected, if any
    if "w" in ctx.invoked_with:
        command["will"] = "w"
    if "c" in ctx.invoked_with:
        command["compact"] = "c"
        if ctx.guild:
            tzimisce.masquerade.database.increment_compact_rolls(ctx.guild.id)

    await tzimisce.masquerade.handle_command(command, ctx)

# Subcommands

@standard_roll.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, arg=None):
    """Set a custom prefix for the guild."""
    if not arg:
        await ctx.send("You must supply a new prefix! To reset to default, use `reset_prefix`.")
        return

    tzimisce.masquerade.database.update_prefix(ctx.guild.id, arg)
    CUSTOM_PREFIXES[ctx.guild.id] = arg

    message = f"Setting the prefix to `{arg}m`."
    if len(arg) > 3:
        message += " A prefix this long might be annoying to type!"

    await ctx.send(message)

@standard_roll.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def reset_prefix(ctx):
    """Reset the guild's prefixes to the defaults."""
    tzimisce.masquerade.database.update_prefix(ctx.guild.id, None)
    CUSTOM_PREFIXES[ctx.guild.id] = None

    await ctx.send("Reset the command prefix to `/m` and `!m`.")

@standard_roll.command(aliases=["coin", "flip", "coinflip",])
async def coin_flip(ctx):
    """Performs a simple coinflip."""
    coin = tzimisce.roll.traditional.roll(1, 2)[0]
    if coin == 1:
        coin = "Heads!"
    else:
        coin = "Tails!"

    await ctx.message.reply(f"{coin}")

@standard_roll.command(name="help")
async def __help(ctx):
    """Displays the basic syntax and a link to the full help file."""

    # We want to display the correct prefix for the server
    prefix = __get_prefix(ctx.guild)[0]
    embed = tzimisce.masquerade.help_embed(prefix)

    await ctx.message.reply(embed=embed)


# Macro-Related. Must be done in a guild.

@standard_roll.command(name="$")
@commands.guild_only()
async def show_stored_rolls(ctx):
    """Displays the user's stored rolls."""
    await tzimisce.masquerade.show_stored_rolls(ctx)

@standard_roll.command(name="$delete-all")
@commands.guild_only()
async def delete_all(ctx):
    """Deletes all of a user's stored rolls."""
    await tzimisce.masquerade.delete_user_rolls(ctx)

# Initiative Manager
initiative_managers = tzimisce.masquerade.database.get_initiative_tables()

@bot.group(invoke_without_command=True, name="mi", aliases=["minit"])
@commands.guild_only()
async def initiative_manager(ctx, mod=None, *, args=None):
    """Displays the initiative table for the current channel."""
    prefix = __get_prefix(ctx.guild)[0]
    usage = "**Initiative Manager Commands**\n"
    usage += f"`{prefix}mi` — Show initiative table (if one exists in this channel)\n"
    usage += f"`{prefix}mi <mod> <character>` — Roll initiative (character optional)\n"
    usage += f"`{prefix}mi dec <action> [-n character]` — Declare an action for a character\n"
    usage += f"`{prefix}mi remove [character]` — Remove initiative (character optional)\n"
    usage += f"`{prefix}mi reroll` — Reroll all initiatives\n"
    usage += f"`{prefix}mi clear` — Clear the table"

    manager = initiative_managers[ctx.channel.id]

    if not mod: # Not rolling
        if manager:
            init_commands = "Commands: remove | reset | clear | declare"
            embed = tzimisce.masquerade.build_embed(
                title="Initiative", footer=init_commands, description=str(manager),
                fields=[]
            )

            content = None
            if ctx.invoked_with == "reroll":
                content = "Rerolling initiative!"
            await ctx.send(content=content, embed=embed)
        else:
            await ctx.message.reply(usage)
    else: # We are rolling initiative
        try:
            is_modifier = mod[0] == "-" or mod[0] == "+"
            mod = int(mod)

            # Add init to manager
            if not manager:
                manager = InitiativeManager()
            character_name = args or ctx.author.display_name

            init = None
            if not is_modifier:
                init = manager.add_init(character_name, mod)
                initiative_managers[ctx.channel.id] = manager
            else:
                init = manager.modify_init(character_name, mod)
                if not init:
                    await ctx.message.reply(f"{character_name} has no initiative to modify!")
                    return

            title = f"{character_name}'s Initiative"

            entry = "entries" if manager.count > 1 else "entry"
            footer = f"{manager.count} {entry} in table. To see initiative: {prefix}mi"

            if is_modifier:
                footer = f"Initiative modified by {mod:+}.\n{footer}"

            embed = tzimisce.masquerade.build_embed(
                title=title, description=str(init), fields=[], footer=footer
            )

            tzimisce.masquerade.database.set_initiative(
                ctx.channel.id, character_name, init.mod, init.die
            )

            await ctx.message.reply(embed=embed)
            tzimisce.masquerade.database.increment_initiative_rolls(ctx.guild.id)
        except ValueError:
            await ctx.message.reply(usage)


@initiative_manager.command(aliases=["reset", "clear", "empty"])
@commands.guild_only()
async def initiative_reset(ctx):
    """Clears the current channel's initiative table."""
    try:
        del initiative_managers[ctx.channel.id]
        tzimisce.masquerade.database.clear_initiative(ctx.channel.id)
        await ctx.message.reply("Reset initiative in this channel!")
    except KeyError:
        await ctx.message.reply("This channel's initiative table is already empty!")

@initiative_manager.command(aliases=["remove", "rm", "delete", "del"])
@commands.guild_only()
async def initiative_remove_character(ctx, *, args=None):
    """Remove a character from initiative manager."""
    manager = initiative_managers[ctx.channel.id]

    if manager:
        character = args or ctx.author.display_name
        removed = manager.remove_init(character)
        if removed:
            tzimisce.masquerade.database.remove_initiative(ctx.channel.id, character)
            message = f"Removed {character} from initiative!"

            if manager.count() == 0:
                del initiative_managers[ctx.channel.id]
                message += "\nNo characters left in initiative. Clearing table."

            await ctx.message.reply(message)
        else:
            await ctx.message.reply(f"Unable to remove {character}; not in initiative!")
    else:
        await ctx.message.reply("Initiative isn't running in this channel!")

@initiative_manager.command(name="reroll")
@commands.guild_only()
async def initiative_reroll(ctx):
    """Rerolls all initiative and prints the new table."""
    manager = initiative_managers[ctx.channel.id]

    if manager:
        manager.reroll()
        await initiative_manager(ctx)

        # Get the new rolls
        characters = manager.characters
        for character in characters:
            init = characters[character]

            tzimisce.masquerade.database.set_initiative(
                ctx.channel.id, character, init.mod, init.die
            )
    else:
        await ctx.send("Initiative isn't set for this channel!")

@initiative_manager.command(name="declare", aliases=["dec"])
@commands.guild_only()
async def initiative_declare(ctx, *args):
    """Declare an initiative action."""
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="+")
    parser.add_argument("-n", "-c", "--name", nargs="+", dest="character")
    parsed = parser.parse_args(args)

    action = " ".join(parsed.action)
    character = ctx.author.display_name
    if parsed.character:
        character = " ".join(parsed.character)

    try:
        manager = initiative_managers[ctx.channel.id]
        if not manager.declare_action(character, action):
            raise NameError(character)

        tzimisce.masquerade.database.set_initiative_action(
            ctx.channel.id, character, action
        )
        await ctx.message.reply(f"Declared action for {character}: {action}.")
    except AttributeError:
        await ctx.message.reply("Initiative isn't set in this channel!")
    except NameError:
        await ctx.message.reply(f"{character} isn't in the initiative table!")

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
            match = tzimisce.masquerade.suggestx.search(message.content)
            if match:
                return match.group("suggestion")

    return None

@bot.event
async def on_reaction_add(reaction, user):
    """Rolls a macro correction suggestion if certain conditions are met."""
    suggestion = suggestion_to_roll(reaction, user)
    if suggestion:
        command = defaultdict(lambda: None)
        match = tzimisce.masquerade.invokex.match(suggestion)
        command.update(match.groupdict())

        ctx = await bot.get_context(reaction.message)
        ctx.author = user # Otherwise, the user is the bot
        await tzimisce.masquerade.handle_command(command, ctx, True)

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
    tzimisce.masquerade.database.add_guild(guild.id, guild.name)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_remove(guild):
    """We don't want to keep track of guilds we no longer belong to."""
    print(f"Removing {guild}.")
    tzimisce.masquerade.database.remove_guild(guild.id)
    await bot.change_presence(activity=discord.Game(__status_message()))

@bot.event
async def on_guild_update(_, after):
    """Sometimes guilds are renamed. Fix that."""
    tzimisce.masquerade.database.rename_guild(after.id, after.name)

@bot.event
async def on_command_error(ctx, error):
    """Ignore CommandNotFound errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.message.reply("Sorry, you don't have permission to do this!")
        return
    if isinstance(error, discord.errors.Forbidden):
        await ctx.message.reply("Permissions error. Please make sure I'm allowed to embed links!")
        __console_log("PERMISSIONS", ctx.message.content)
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Sorry, this command isn't available in DMs!")
        return
    if isinstance(error, commands.CommandInvokeError):
        if "IndexError" in str(error):
            await ctx.message.reply("You forgot your syntax!")
            return

    # Unknown error; print invoking message and raise
    __console_log("UNKNOWN", ctx.message.content)

    raise error

def __console_log(header, message):
    """Prints an offending user invocation to the console."""
    print(header)
    print("\n\n**********************")
    print(f"{header} ERROR ON {message}")
    print("**********************\n\n")

# Misc

def __get_prefix(guild) -> tuple:
    """Returns the guild's prefix. If the guild is None, returns a default."""
    default_prefixes = ("/", "!")

    if guild:
        prefix = CUSTOM_PREFIXES[guild.id]
        if prefix:
            return (prefix,)
        return default_prefixes

    return default_prefixes

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
