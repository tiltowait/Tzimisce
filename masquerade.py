"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict
from typing import Optional

import discord
from dotenv import load_dotenv
import topgg
import pymongo
import statcord
from discord.ext import commands

import storyteller


# Setup

load_dotenv()

async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return storyteller.settings.get_prefixes(message.guild)


if (debug_guilds := os.getenv('DEBUG')) is not None:
    print("Debugging on", debug_guilds)
    debug_guilds = [int(debug_guilds)]

bot = commands.Bot(
    command_prefix=determine_prefix,
    case_insensitive=True,
    debug_guilds=debug_guilds
)

bot.remove_command("help")

# Statcord
if "STATCORD" in os.environ:
    api = statcord.Client(bot, os.environ["STATCORD"])
    api.start_loop()
else:
    api = None

PLAYER_COL = pymongo.MongoClient(os.environ["TZIMISCE_MONGO"]).tzimisce.interactions


@bot.event
async def on_message(message):
    """Determines how to handle messages."""
    if message.author == bot.user:
        return

    # Make sure the user is invoking the bot
    prefixes = storyteller.settings.get_prefixes(message.guild)
    used_prefix = None
    for prefix in prefixes:
        if message.clean_content.startswith(prefix):
            used_prefix = prefix
            break
    if not used_prefix:
        return

    updated_prefix = f"{used_prefix}m" # Standardize to internal prefix
    content = message.clean_content.removeprefix(used_prefix)
    components = content.split()

    # While most commands require a space between m and the command, minit does
    # not. Thus, we need to check if the first argument given is a valid command.
    # If not, then we add a space between the prefix and the command.
    #
    # Example transformations (if prefix is !!)
    # !!5 -> !!m5 -> !!m 5
    # !!coin -> !!mcoin -> !!m coin
    # !!init -> !!minit

    if len(components) == 0:
        command = "help"
    else:
        command = components[0]

    if not bot.get_command(f"m{command}"):
        content = f"{updated_prefix} {content}"
    else:
        content = f"{updated_prefix}{content}"

    message.content = content
    await bot.process_commands(message)

    # Log the interaction
    PLAYER_COL.insert_one({ "guild": message.guild.name, "user": message.author.id })


# Commands

# This is only temporary until May 2022

async def slash_command_info(ctx, repl):
    """Print a message about slash commands."""
    await ctx.reply(
        f"Due to upcoming Discord changes, this command has been replaced with `{repl}`."
    )


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
    command = "mw" if "w" in ctx.invoked_with else "mm"
    if "z" in ctx.invoked_with:
        command = "z" + command
    if "c" in ctx.invoked_with:
        command = "c" + command

    await slash_command_info(ctx, f"/{command}")


# Subcommands

@standard_roll.command(aliases=["set", "setting"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def settings(ctx, *args):
    """Fetch or update server settings."""

    # Display settings
    if len(args) < 1:
        prefix = storyteller.settings.get_prefixes(ctx.guild.id)[0]
        msg = []
        for param in storyteller.settings.available_parameters:
            value = storyteller.settings.value(ctx.guild.id, param)
            msg.append(f"`{param}`: `{value}`")
        msg = "\n".join(msg)
        details = f"For more info or to set: `{prefix} settings <parameter> [value]`"

        await ctx.reply(f"This server's settings:\n{msg}\n{details}")
        return

    if len(args) > 2:
        await ctx.reply("Error! Too many arguments.")
        return

    # Display or update indivitual settings
    key = args[0]
    try:
        # Display
        if len(args) < 2:
            value = storyteller.settings.value(ctx.guild.id, key)
            info = storyteller.settings.parameter_information(key)
            await ctx.reply(f"{info} (Current: `{value}`)")
        # Update
        else:
            new_value = args[1]
            if key == storyteller.settings.PREFIX and new_value == "reset":
                new_value = None

            message = storyteller.settings.update(ctx.guild.id, key, new_value)
            await ctx.reply(message)
    except ValueError as error:
        await ctx.reply(error)


@standard_roll.command(aliases=["coin", "flip", "coinflip",])
async def coin_flip(ctx):
    """Performs a simple coinflip."""
    await slash_command_info(ctx, "/coinflip")


@standard_roll.command()
async def chance(ctx):
    """Roll a chance die (primarily for CofD games)."""
    await slash_command_info(ctx, "/chance")


@standard_roll.command(name="help")
async def __help(ctx):
    """Displays the basic syntax and a link to the full help file."""
    await slash_command_info(ctx, "/help")


# Macro-Related. Must be done in a guild.

@standard_roll.command(name="$")
@commands.guild_only()
async def show_stored_rolls(ctx):
    """Displays the user's stored rolls."""
    await storyteller.engine.show_stored_rolls(ctx)


@standard_roll.command(name="$delete-all")
@commands.guild_only()
async def delete_all(ctx):
    """Deletes all of a user's stored rolls."""
    macro_count, meta_count = storyteller.engine.macro_counts(ctx)
    prompt = "Are you sure you wish to delete your macros on this server? Click ✅ to confirm."

    # Correctly pluralize and display number of macros/metamacros to delete
    newline = ""
    notice = ""
    if macro_count > 0:
        newline = "\n"
        notice = f"**{macro_count}** macro"
        if macro_count > 1:
            notice += "s"

    if meta_count > 0:
        newline = "\n"
        prompt_addition = f" and **{meta_count}** meta-macro"
        if meta_count > 1:
            prompt_addition += "s"

        notice = f"{notice}{prompt_addition}"

    prompt += f"{newline}{notice} will be deleted."
    message = await ctx.reply(prompt)

    await message.add_reaction("✅")
    await message.add_reaction("❌")


# Statistics

@standard_roll.command(aliases=["stats"])
async def statistics(ctx, *args):
    """Prints statistics for a given dice pool."""
    usage = "Expected arguments: <pool> <difficulty> <target>"
    try:
        args = list(args)
        pool = int(args.pop(0))
        diff = int(args.pop(0))
        target = 1

        if len(args) > 0:
            target = int(args.pop(0))

        # Check our constraints
        if not 1 <= pool <= 30:
            raise ValueError("Error! Pool must be between 1-30!")

        if not 2 <= diff <= 10:
            raise ValueError("Error! Difficulty must be between 2-10!")

        if not 1 <= target <= (pool * 2):
            raise ValueError("Error! Success target must be between 1 and twice your pool!")

        prob = storyteller.probabilities.get_probabilities(pool, diff, target)

        # Properly pluralize "successes", when applicable
        success = "success"
        if target > 1:
            success += "es"

        title = f"Statistics for {target} {success} at {pool} v {diff}"
        embed = discord.Embed(title=title)

        standard = f"**Average successes:** {prob.avg:.3}\n"
        standard += f"**{target}+ {success}:** {prob.prob:.3%}\n"
        standard += f"**Using Willpower:** {prob.prob_wp:.3%}\n"
        standard += f"**Total Failure:** {prob.fail:.3%}\n"
        standard += f"**Botch:** {prob.botch:.3%}"

        spec = f"**Average successes:** {prob.avg_spec:.3}\n"
        spec += f"**{target}+ {success}:** {prob.prob_spec:.3%}\n"
        spec += f"**Using Willpower:** {prob.prob_spec_wp:.3%}\n"
        spec += f"**Total Failure:** {prob.fail_spec:.3%}\n"
        spec += f"**Botch:** {prob.botch:.3%}"

        embed.add_field(name="Standard Roll", value=standard, inline=False)
        embed.add_field(name="With Specialty", value=spec, inline=False)

        await ctx.reply(embed=embed)
    except IndexError:
        await ctx.reply(usage)
    except ValueError as error:
        await ctx.reply(f"{error}\n{usage}")

    # Log statistics
    if ctx.guild:
        storyteller.engine.statistics.increment_stats_calculated(ctx.guild)


# Initiative Management

init_aliases = ["minit", "mcinit", "mci", "minitc", "mic"]
@bot.group(invoke_without_command=True, name="mi", aliases=init_aliases, case_insensitive=True)
@commands.guild_only()
async def initiative_manager(ctx, mod: str=None, *, character: str=None, use_embed: bool=None):
    """Displays the initiative table for the current channel."""

    if use_embed is None:
        use_embed = not __use_compact_mode(ctx.invoked_with, ctx.guild.id)

    # Parse the command
    response = storyteller.parse.initiative(ctx, mod, character, use_embed)
    if response.both_set:
        await ctx.send(content=response.content, embed=response.embed)
    else:
        await ctx.reply(content=response.content, embed=response.embed)


@initiative_manager.command(aliases=["reset", "clear", "empty"])
@commands.guild_only()
async def initiative_reset(ctx):
    """Clears the current channel's initiative table."""
    try:
        storyteller.initiative.remove_table(ctx.channel.id)
        await ctx.reply("Reset initiative in this channel!")
    except KeyError:
        await ctx.reply("This channel's initiative table is already empty!")


@initiative_manager.command(aliases=["remove", "rm", "delete", "del"])
@commands.guild_only()
async def initiative_remove_character(ctx, *, character_name=None):
    """Remove a character from initiative manager."""
    response = storyteller.parse.initiative_removal(ctx, character_name)
    await ctx.reply(content=response.content, embed=response.embed)


@initiative_manager.command(name="reroll")
@commands.guild_only()
async def initiative_reroll(ctx):
    """Rerolls all initiative and prints the new table."""
    manager = storyteller.initiative.get_table(ctx.channel.id)

    if manager:
        # Reroll and store the new initiatives before displaying
        manager.reroll()

        for character, init in manager.characters.items():
            storyteller.initiative.set_initiative(
                ctx.guild.id, ctx.channel.id, character, init.mod, init.die
            )

        # discord.py provides no means of checking which alias was used to invoke
        # a subcommand, so we have to manipulate the raw message string itself by
        # removing the bot prefix from the message and passing that to
        # __use_compact_mode() instead of passing the simpler ctx.invoked_with.
        #
        # Technically, this means the user can accidentally toggle compact mode
        # by supplying arguments *after* "reroll"; however, as doing so is far
        # from the end of the world, we won't care about that.
        prefix = ctx.prefix
        command = ctx.message.content.replace(prefix, "")
        use_embed = not __use_compact_mode(command, ctx.guild.id)

        await initiative_manager(ctx, use_embed=use_embed) # Print the new initiative table
    else:
        await ctx.send("Initiative isn't set for this channel!")


@initiative_manager.command(name="declare", aliases=["dec"])
@commands.guild_only()
async def initiative_declare(ctx, *args):
    """Declare an initiative action."""
    try:
        storyteller.parse.initiative_declare(ctx, args)
        await ctx.message.add_reaction("👍")
        await ctx.message.add_reaction("⚔️")
    except SyntaxError as error:
        await ctx.reply(error)


# Events

def __is_valid_reaction(reaction, user, emoji):
    """Determines if the correct user clicked the correct reaction."""
    if reaction.emoji == emoji and reaction.message.author == bot.user:
        return user in reaction.message.mentions
    return False


def suggestion_to_roll(reaction, user):
    """Returns a suggested macro if the correct user replies with a thumbsup."""
    if __is_valid_reaction(reaction, user, "👍"):
        match = storyteller.engine.suggestx.search(reaction.message.content)
        if match:
            return match.group("suggestion")

    return None


@bot.event
async def on_reaction_add(reaction, user):
    """Rolls a macro correction suggestion if certain conditions are met."""
    suggestion = suggestion_to_roll(reaction, user)
    if suggestion:
        command = defaultdict(lambda: None)
        match = storyteller.engine.invokex.match(suggestion)
        command.update(match.groupdict())

        # Get the server settings
        guild_settings = storyteller.settings.settings_for_guild(reaction.message.guild)
        command.update(guild_settings)

        await reaction.message.delete()

        # We are going to try to reply to the original invocation message. If
        # that fails, then we will simply @ the user.
        ctx = await __get_reaction_message_reference_context(reaction, user)
        ctx.author = user

        await storyteller.engine.handle_command(command, ctx)
    elif __is_valid_reaction(reaction, user, "✅"):
        ctx = await __get_reaction_message_reference_context(reaction, user)
        await storyteller.engine.delete_user_rolls(ctx)
        await reaction.message.delete()
    elif __is_valid_reaction(reaction, user, "❌"):
        await reaction.message.delete()


async def __get_reaction_message_reference_context(reaction, user):
    """Returns the context of the message replied to in the reaction's message."""
    ctx = await bot.get_context(reaction.message)
    try:
        msg = await ctx.fetch_message(reaction.message.reference.message_id)
        ctx = await bot.get_context(msg)
        return ctx
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        # If the above fails, we return the reaction's message context and zero out the content."""
        ctx.author = user
        ctx.message.content = None
        return ctx


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
    storyteller.settings.add_guild(guild.id)
    storyteller.engine.statistics.add_guild(guild.id, guild.name)
    await bot.change_presence(activity=discord.Game(__status_message()))


@bot.event
async def on_guild_remove(guild):
    """We don't want to keep track of guilds we no longer belong to."""
    print(f"Removing {guild}.")
    storyteller.settings.remove_guild(guild.id)
    await bot.change_presence(activity=discord.Game(__status_message()))


@bot.event
async def on_guild_update(_, after):
    """Sometimes guilds are renamed. Fix that."""
    storyteller.engine.statistics.rename_guild(after.id, after.name)


@bot.event
async def on_guild_channel_delete(channel):
    """Removes initiative from the deleted channel."""
    storyteller.initiative.remove_table(channel.id)


@bot.event
async def on_command(ctx):
    """Post to Statcord."""
    if api is not None:
        api.command_run(ctx)


@bot.event
async def on_command_error(ctx, error):
    """Ignore CommandNotFound errors."""
    # pylint: disable=too-many-return-statements
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("Sorry, you don't have permission to do this!")
        return
    if isinstance(error, discord.errors.Forbidden):
        await __alert_permissions(ctx)
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Sorry, this command isn't available in DMs!")
        return
    if isinstance(error, commands.CommandInvokeError):
        if "Forbidden" in str(error):
            await __alert_permissions(ctx)
            return
        if "reply" in str(error):
            await ctx.send("Error! Please ensure I have permission to read message history.")
            return
        if "IndexError" in str(error):
            await ctx.reply("You forgot your syntax!")
            return
    if isinstance(error, commands.UnexpectedQuoteError):
        # A bug in the library (1.7.2) prevents certain iOS smart quotes from
        # being handled correctly. Thus far, I have found it doesn't like English
        # single quotes, but there may be more. When we encounter this error,
        # we will replace the smart quote with a dumb one.
        #
        # Unfortunately, this causes another glitch: when working with command
        # arguments, discord.py will drop the arguments before (and sometimes
        # after) the offending quote. Rather than write a nasty workaround,
        # we are going to let the bug lie for the time being, given its rarity.
        # A bug has been filed on GitHub.
        if hasattr(ctx, 'coerced_quotes'):
            return

        ios_quotes = ["‘","’"]
        ios_quote_found = False

        for quote in ios_quotes:
            if quote in ctx.message.content:
                content = ctx.message.clean_content.replace(quote, "'")
                ctx.message.content = content

                ios_quote_found = True

        if ios_quote_found:
            await bot.invoke(ctx)
            return

    # Unknown error; print invoking message and raise
    chat = ctx.guild.name if ctx.guild else "DM"
    print("\n\n**********************")
    print(f"{chat}: UNKNOWN ERROR ON {ctx.message.content}")
    print("**********************\n\n")

    raise error


async def __alert_permissions(ctx):
    """Alerts the user to the required permissions."""
    if ctx.channel.permissions_for(ctx.me).send_messages:
        msg = "Permissions error. Please make sure I can embed links,"
        msg += " read message history, and add reactions!"
        await ctx.send(msg)


# Misc Functions

def __status_message():
    """Sets the bot's Discord presence message."""
    servers = len(bot.guilds)
    return f"!m help | {servers} chronicles"


def __use_compact_mode(invocation: str, guildid: Optional[int]) -> bool:
    """
    Determine whether a command should use compact mode.
    Args:
        invocation (str): The string used to invoke the command
        guildid (Optional[int]): The Discord ID of the guild where the bot was invoked
    Returns (bool): True if the bot should use compact mode
    """

    # Note that some care must be taken when passing the bot invocation. Some commands,
    # such as "coin" and "chance", always have a 'c' in them. In these instances, it is
    # safest simply to pass an empty string.
    if "c" in invocation:
        return True

    guild_settings = storyteller.settings.settings_for_guild(guildid)
    return guild_settings["use_compact"]


# END BOT DEFINITIONS

bot.load_extension("roll_commands")
bot.load_extension("misc_commands")

if __name__ == "__main__":
    # Track guild count in top.gg. Only do this in production, not in dev setting
    if (topgg_token := os.getenv("TOPGG_TOKEN")) is not None:
        print("Establishing top.gg connection.")
        bot.dblpy = topgg.DBLClient(bot, topgg_token, autopost=True)

    bot.run(os.environ["TZIMISCE_TOKEN"])
