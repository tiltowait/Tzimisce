"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict
from distutils.util import strtobool
import argparse

import discord
from discord.ext import commands

import tzimisce
from tzimisce.initiative import InitiativeManager

# Setup

async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return tzimisce.settings.get_prefix(message.guild)

bot = commands.Bot(command_prefix=determine_prefix)
bot.remove_command("help")

# Commands

# m - Invoke a roll
# w - Use Willpower
# c - Use compact mode
# z - Disable botches
standard_aliases = [
    "mw", "mc", "mz",
    "mwz", "mzw", "mcz", "mzc", "mwc", "mcw",
    "mzcw", "mzwc", "mwzc", "mczw", "mcwz", "mwcz"
]

@bot.group(invoke_without_command=True, name="m", aliases=standard_aliases)
async def standard_roll(ctx, *, args=None):
    """Primary function. Perform a pool or traditional roll."""
    if not args:
        await __help(ctx)
        return

    # Split the comment from the syntax
    content = ctx.message.clean_content.split(" ", 1)[1] # Just the command arguments
    content = content.split("#", 1) # Split out the comment from the syntax
    syntax = content[0]
    comment = content[1] if len(content) > 1 else None

    if len(syntax) == 0: # Can happen if user supplies a comment without syntax
        raise IndexError

    command = defaultdict(lambda: None)
    command["syntax"] = syntax.strip()
    command["comment"] = comment.strip() if comment else None

    guild_settings = tzimisce.settings.settings_for_guild(ctx.guild.id)
    command.update(guild_settings)

    # See what options the user has selected, if any
    if "w" in ctx.invoked_with:
        command["will"] = "w"
    if "c" in ctx.invoked_with or guild_settings["use_compact"]:
        command["compact"] = "c"
        if ctx.guild:
            tzimisce.masquerade.database.increment_compact_rolls(ctx.guild.id)

    # If the bot doesn't have embed permissions, then we don't want to count that in the stats
    if not ctx.channel.permissions_for(ctx.me).embed_links:
        command["compact"] = "c"

    if "z" in ctx.invoked_with:
        command["no_botch"] = "z"

    await tzimisce.masquerade.handle_command(command, ctx)

# Subcommands

@standard_roll.command(aliases=["set", "setting"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def settings(ctx, *args):
    """Fetch or update server settings."""
    params = tzimisce.settings.available_parameters()

    # Display settings
    if len(args) < 1:
        prefix = tzimisce.settings.get_prefix(ctx.guild.id)[0]
        msg = []
        for param in params:
            value = tzimisce.settings.value(ctx.guild.id, param)
            msg.append(f"`{param}`: `{value}`")
        msg = "\n".join(msg)
        details = f"For more info or to set: `{prefix}m settings <parameter> [value]`"

        await ctx.reply(f"This server's settings:\n{msg}\n{details}")
        return

    if len(args) > 2:
        await ctx.reply("Error! Too many arguments.")
        return

    # Display or update indivitual settings
    key = args[0]
    if key in params:
        if len(args) < 2:
            value = tzimisce.settings.value(ctx.guild.id, key)
            info = tzimisce.settings.parameter_information(key)
            await ctx.reply(f"{info} (Current: `{value}`)")
        else:
            new_value = args[1]

            # Prefixes aren't true/false
            if key != tzimisce.settings.PREFIX:
                try:
                    new_value = bool(strtobool(new_value))
                    tzimisce.settings.update(ctx.guild.id, key, new_value)
                except ValueError:
                    await ctx.reply(f"Error! `{key}` must be `true` or `false`!")
                    return

                await ctx.reply(f"Setting `{key}` to `{new_value}`!")
            else:
                if new_value == "reset":
                    await __reset_prefix(ctx)
                else:
                    await __set_prefix(ctx, new_value)
    else:
        await ctx.reply(f"Unknown setting `{key}`!")

async def __set_prefix(ctx, new_value):
    """Set a custom prefix for the guild."""
    tzimisce.settings.update(ctx.guild.id, tzimisce.settings.PREFIX, new_value)

    message = f"Setting the prefix to `{new_value}m`."
    if len(new_value) > 3:
        message += " A prefix this long might be annoying to type!"

    await ctx.send(message)

async def __reset_prefix(ctx):
    """Reset the current guild's prefix."""
    tzimisce.settings.update(ctx.guild.id, tzimisce.settings.PREFIX, None)

    await ctx.send("Reset the command prefix to `/m` and `!m`.")


@standard_roll.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def set_prefix(ctx):
    """DEPRECATED: User should use /m settings prefix."""
    prefix = tzimisce.settings.get_prefix(ctx.guild.id)[0]
    await ctx.reply(f"This function has moved! Use `{prefix}m settings prefix`.")

@standard_roll.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def reset_prefix(ctx):
    """Reset the guild's prefixes to the defaults."""
    prefix = tzimisce.settings.get_prefix(ctx.guild.id)[0]
    await ctx.reply(f"This function has moved! Use `{prefix}m settings prefix reset`.")

@standard_roll.command(aliases=["coin", "flip", "coinflip",])
async def coin_flip(ctx):
    """Performs a simple coinflip."""
    coin = tzimisce.roll.traditional.roll(1, 2)[0]
    if coin == 1:
        coin = "Heads!"
    else:
        coin = "Tails!"

    await ctx.reply(f"{coin}")

@standard_roll.command(name="help")
async def __help(ctx):
    """Displays the basic syntax and a link to the full help file."""

    # We want to display the correct prefix for the server
    prefix = tzimisce.settings.get_prefix(ctx.guild)[0]
    embed = tzimisce.masquerade.help_embed(prefix)

    await ctx.reply(embed=embed)


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

# Initiative Management

@bot.group(invoke_without_command=True, name="mi", aliases=["minit"])
@commands.guild_only()
async def initiative_manager(ctx, mod=None, *, args=None):
    """Displays the initiative table for the current channel."""
    prefix = tzimisce.settings.get_prefix(ctx.guild)[0]
    usage = "**Initiative Manager Commands**\n"
    usage += f"`{prefix}mi` — Show initiative table (if one exists in this channel)\n"
    usage += f"`{prefix}mi <mod> <character>` — Roll initiative (character optional)\n"
    usage += f"`{prefix}mi dec <action> [-n character]` — Declare an action for a character\n"
    usage += f"`{prefix}mi remove [character]` — Remove initiative (character optional)\n"
    usage += f"`{prefix}mi reroll` — Reroll all initiatives\n"
    usage += f"`{prefix}mi clear` — Clear the table"

    manager = tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]

    if not mod: # Not rolling
        if manager:
            init_commands = "Commands: remove | clear | reroll | declare"
            embed = tzimisce.masquerade.build_embed(
                title="Initiative", footer=init_commands, description=str(manager),
                fields=[]
            )

            content = None
            if ctx.invoked_with == "reroll":
                content = "Rerolling initiative!"
            await ctx.send(content=content, embed=embed)
        else:
            await ctx.reply(usage)
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
                tzimisce.INITIATIVE_MANAGERS[ctx.channel.id] = manager
            else:
                init = manager.modify_init(character_name, mod)
                if not init:
                    await ctx.reply(f"{character_name} has no initiative to modify!")
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

            await ctx.reply(embed=embed)
            tzimisce.masquerade.database.increment_initiative_rolls(ctx.guild.id)
        except ValueError:
            await ctx.reply(usage)


@initiative_manager.command(aliases=["reset", "clear", "empty"])
@commands.guild_only()
async def initiative_reset(ctx):
    """Clears the current channel's initiative table."""
    try:
        del tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]
        tzimisce.masquerade.database.clear_initiative(ctx.channel.id)
        await ctx.reply("Reset initiative in this channel!")
    except KeyError:
        await ctx.reply("This channel's initiative table is already empty!")

@initiative_manager.command(aliases=["remove", "rm", "delete", "del"])
@commands.guild_only()
async def initiative_remove_character(ctx, *, args=None):
    """Remove a character from initiative manager."""
    manager = tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]

    if manager:
        character = args or ctx.author.display_name
        removed = manager.remove_init(character)
        if removed:
            tzimisce.masquerade.database.remove_initiative(ctx.channel.id, character)
            message = f"Removed {character} from initiative!"

            if manager.count == 0:
                del tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]
                message += "\nNo characters left in initiative. Clearing table."

            await ctx.reply(message)
        else:
            await ctx.reply(f"Unable to remove {character}; not in initiative!")
    else:
        await ctx.reply("Initiative isn't running in this channel!")

@initiative_manager.command(name="reroll")
@commands.guild_only()
async def initiative_reroll(ctx):
    """Rerolls all initiative and prints the new table."""
    manager = tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]

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

    try:
        parsed = parser.parse_args(args)

        action = " ".join(parsed.action)
        character = ctx.author.display_name
        if parsed.character:
            character = " ".join(parsed.character)

        manager = tzimisce.INITIATIVE_MANAGERS[ctx.channel.id]
        if not manager.declare_action(character, action):
            raise NameError(character)

        tzimisce.masquerade.database.set_initiative_action(
            ctx.channel.id, character, action
        )
        await ctx.message.add_reaction("👍")
        await ctx.message.add_reaction("⚔️")
    except AttributeError:
        await ctx.reply("Initiative isn't set in this channel!")
    except NameError:
        await ctx.reply(f"{character} isn't in the initiative table!")
    except SystemExit:
        await ctx.reply("Usage: `/mi dec <action> [-n character]`")

# Events

def suggestion_to_roll(reaction, user):
    """Returns a suggested macro if the correct user replies with a thumbsup."""
    message = reaction.message
    if reaction.emoji == "👍" and message.author == bot.user:
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

        await reaction.message.delete()

        # We are going to try to reply to the original invocation message. If
        # that fails, then we will simply @ the user.
        ctx = await bot.get_context(reaction.message)
        reference = reaction.message.reference

        try:
            msg = await ctx.fetch_message(reference.message_id)
            ctx = await bot.get_context(msg)
            ctx.author = user # Otherwise, the user is the bot
            await tzimisce.masquerade.handle_command(command, ctx, False)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            ctx.author = user
            await tzimisce.masquerade.handle_command(command, ctx, True)

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
        await ctx.reply("Sorry, you don't have permission to do this!")
        return
    if isinstance(error, discord.errors.Forbidden):
        await ctx.reply("Permissions error. Please make sure I'm allowed to embed links!")
        __console_log("PERMISSIONS", ctx.message.content)
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Sorry, this command isn't available in DMs!")
        return
    if isinstance(error, commands.CommandInvokeError):
        if "IndexError" in str(error):
            await ctx.reply("You forgot your syntax!")
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

def __status_message():
    """Sets the bot's Discord presence message."""
    servers = len(bot.guilds)
    return f"/m help | {servers} chronicles"


# End definitions
bot.run(os.environ["TZIMISCE_TOKEN"])
