"""Creates and connects an instance of the Tzimisce dicebot."""

import logging
import os

import discord
import statcord
from discord.ext import commands
from dotenv import load_dotenv

import storyteller

# Setup

load_dotenv()

logging.basicConfig(level=logging.INFO)


async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return storyteller.settings.get_prefixes(message.guild)


if (debug_guild := os.getenv("DEBUG")) is not None:
    logging.info("Debugging on %s", debug_guild)
    debug_guild = [int(debug_guild)]

intents = discord.Intents(guilds=True, members=True)

bot = commands.AutoShardedBot(
    command_prefix=determine_prefix,
    case_insensitive=True,
    debug_guilds=debug_guild,
    intents=intents,
)

bot.remove_command("help")

# Statcord
if (statcord_token := os.getenv("STATCORD")) is not None:
    api = statcord.Client(bot, statcord_token)
    api.start_loop()
else:
    api = None


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

    updated_prefix = f"{used_prefix}m"  # Standardize to internal prefix
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


# Events


@bot.event
async def on_ready():
    """Print a message letting us know the bot logged in to Discord."""
    logging.info("Logged on as %s!", bot.user)
    logging.info("Playing on %s servers.", len(bot.guilds))
    logging.info(discord.version_info)

    await bot.change_presence(activity=discord.Game(__status_message()))


@bot.event
async def on_guild_join(guild):
    """When joining a guild, log it for statistics purposes."""
    logging.info("Joining %s!", guild)
    storyteller.settings.add_guild(guild.id)
    storyteller.engine.statistics.add_guild(guild.id, guild.name)
    await bot.change_presence(activity=discord.Game(__status_message()))


@bot.event
async def on_guild_remove(guild):
    """We don't want to keep track of guilds we no longer belong to."""
    logging.info("Removing %s.", guild)
    storyteller.settings.remove_guild(guild.id)
    await bot.change_presence(activity=discord.Game(__status_message()))


@bot.event
async def on_guild_update(before, after):
    """Sometimes guilds are renamed. Fix that."""
    if before.name != after.name:
        storyteller.engine.statistics.rename_guild(after.id, after.name)


@bot.event
async def on_guild_channel_delete(channel):
    """Removes initiative from the deleted channel."""
    storyteller.initiative.remove_table(channel.id)


@bot.event
async def on_application_command(ctx):
    """Post to Statcord."""
    if api is not None:
        api.command_run(ctx)


@bot.event
async def on_application_command_error(ctx, error):
    """Inform user of errors."""
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.respond("Sorry, this can't be done in DMs.", ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("Sorry, you don't have permission to do this.", ephemeral=True)
    else:
        raise error


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
        if hasattr(ctx, "coerced_quotes"):
            return

        ios_quotes = ["‘", "’"]
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
    logging.error("%s: UNKNOWN ERROR ON %s", chat, ctx.message.content)

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
    return f"/help | {servers} chronicles"


# END BOT DEFINITIONS

for filename in os.listdir("./interface"):
    if filename.endswith(".py"):
        bot.load_extension(f"interface.{filename[:-3]}")


if __name__ == "__main__":
    # Track guild count in top.gg. Only do this in production, not in dev setting
    bot.run(os.environ["TZIMISCE_TOKEN"])
