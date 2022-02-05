"""Creates and connects an instance of the Tzimisce dicebot."""

import os

import discord
from dotenv import load_dotenv
import topgg
import statcord
from discord.ext import commands

import storyteller


# Setup

load_dotenv()

async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return storyteller.settings.get_prefixes(message.guild)


if (debug_guild := os.getenv('DEBUG')) is not None:
    print("Debugging on", debug_guild)
    debug_guild = [int(debug_guild)]

intents = discord.Intents.default()
#intents.members = True

bot = commands.Bot(
    command_prefix=determine_prefix,
    case_insensitive=True,
    debug_guilds=debug_guild,
    intents=intents
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


# Commands

# This is only temporary until May 2022

class DocumentationLink(discord.ui.View):
    """A simple view that shows a link to the documentation."""

    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="More Information",
            url="https://www.storyteller-bot.com/#/"
        ))
        self.add_item(discord.ui.Button(
            label="Re-Invite [Tzimisce]",
            url="https://discord.com/api/oauth2/authorize?client_id=642775025770037279&permissions=2147764224&scope=applications.commands%20bot"
        ))


    @discord.ui.button(label="Disable This Message", style=discord.ButtonStyle.danger)
    async def slash_warning_disable(self, _, interaction):
        """Disable the slash warning by changing the prefix."""
        if interaction.user.guild_permissions.administrator:
            storyteller.settings.update(interaction.guild.id, "prefix", ".,/;m")
            await interaction.response.edit_message(
                content="Slash command warnings are now disabled.",
                view=None
            )
        else:
            await interaction.response.send_message(
                "Only the server admin may do this!",
                ephemeral=True
            )


async def slash_command_info(ctx, *repls):
    """Print a message about slash commands."""
    repls = " or ".join(repls)
    msg = f"```NEW COMMAND: {repls}```"
    msg += "\nDue to upcoming Discord changes, this command has been replaced."
    msg += "Slash commands not working? Try clicking the button to re-invite [Tzimisce]."
    msg += "\n\n**You may need to *remove* the bot before re-inviting!** In addition, the"
    msg += " `@everyone` role needs the *Use Slash Commands* permission."

    await ctx.reply(msg, view=DocumentationLink())


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
async def standard_roll(ctx):
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
async def settings(ctx):
    """Fetch or update server settings."""
    await slash_command_info(ctx, "/settings")


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
    await slash_command_info(ctx, "/macros list")


@standard_roll.command(name="$delete-all")
@commands.guild_only()
async def delete_all(ctx):
    """Deletes all of a user's stored rolls."""
    await slash_command_info(ctx, "/macros purge")


# Statistics

@standard_roll.command(aliases=["stats"])
async def statistics(ctx):
    """Prints statistics for a given dice pool."""
    await slash_command_info(ctx, "/stats")


# Initiative Management

init_aliases = ["minit", "mcinit", "mci", "minitc", "mic"]
@bot.group(invoke_without_command=True, name="mi", aliases=init_aliases, case_insensitive=True)
@commands.guild_only()
async def initiative_manager(ctx):
    """Displays the initiative table for the current channel."""
    await slash_command_info(ctx, "/init show", "/init add")


@initiative_manager.command(aliases=["reset", "clear", "empty"])
@commands.guild_only()
async def initiative_reset(ctx):
    """Clears the current channel's initiative table."""
    await slash_command_info(ctx, "/init clear")


@initiative_manager.command(aliases=["remove", "rm", "delete", "del"])
@commands.guild_only()
async def initiative_remove_character(ctx):
    """Remove a character from initiative manager."""
    await slash_command_info(ctx, "/init rm")


@initiative_manager.command(name="reroll")
@commands.guild_only()
async def initiative_reroll(ctx):
    """Rerolls all initiative and prints the new table."""
    await slash_command_info(ctx, "/init reroll")


@initiative_manager.command(name="declare", aliases=["dec"])
@commands.guild_only()
async def initiative_declare(ctx):
    """Declare an initiative action."""
    await slash_command_info(ctx, "/init dec")


# Events


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
    #storyteller.settings.remove_guild(guild.id)
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
    if isinstance(error.original, commands.NoPrivateMessage):
        await ctx.respond("Sorry, this can't be done in DMs.", ephemeral=True)
    elif isinstance(error.original, commands.MissingPermissions):
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
    return f"/help | {servers} chronicles"


# END BOT DEFINITIONS

for filename in os.listdir("./interface"):
    if filename.endswith(".py"):
        bot.load_extension(f"interface.{filename[:-3]}")


if __name__ == "__main__":
    # Track guild count in top.gg. Only do this in production, not in dev setting
    if (topgg_token := os.getenv("TOPGG_TOKEN")) is not None:
        print("Establishing top.gg connection.")
        bot.dblpy = topgg.DBLClient(bot, topgg_token, autopost=True)

    bot.run(os.environ["TZIMISCE_TOKEN"])
