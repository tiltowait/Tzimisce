"""Creates and connects an instance of the Tzimisce dicebot."""

import os
from collections import defaultdict

import discord
from discord.ext import commands

import storyteller

# Setup

async def determine_prefix(_, message):
    """Determines the correct command prefix for the guild."""
    return storyteller.settings.get_prefixes(message.guild)

bot = commands.Bot(command_prefix=determine_prefix, case_insensitive=True)
bot.remove_command("help")

@bot.event
async def on_message(message):
    """Determines how to handle messages."""

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
    content = ctx.message.content.split(" ", 1)[1] # Just the command arguments
    content = content.split("#", 1) # Split out the comment from the syntax
    syntax = content[0]
    comment = content[1] if len(content) > 1 else None

    if len(syntax) == 0: # Can happen if user supplies a comment without syntax
        raise IndexError

    command = defaultdict(lambda: None)
    command["syntax"] = " ".join(syntax.split())
    command["comment"] = " ".join(comment.split()) if comment else None

    guild_settings = storyteller.settings.settings_for_guild(ctx.guild)
    command.update(guild_settings)

    # See what options the user has selected, if any
    if "w" in ctx.invoked_with:
        command["will"] = "w"
    if "c" in ctx.invoked_with or guild_settings["use_compact"]:
        command["compact"] = "c"
        if ctx.guild:
            storyteller.engine.statistics.increment_compact_rolls(ctx.guild.id)

    # If the bot doesn't have embed permissions, then we don't want to count that in the stats
    if not ctx.channel.permissions_for(ctx.me).embed_links:
        command["compact"] = "c"

    if "z" in ctx.invoked_with:
        command["no_botch"] = "z"

    await storyteller.engine.handle_command(command, ctx)

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
    coin = storyteller.roll.traditional.roll(1, 2)[0]
    if coin == 1:
        coin = "Heads!"
    else:
        coin = "Tails!"

    await ctx.reply(f"{coin}")

@standard_roll.command(name="help")
async def __help(ctx):
    """Displays the basic syntax and a link to the full help file."""

    # We want to display the correct prefix for the server
    prefix = storyteller.settings.get_prefixes(ctx.guild)[0]
    embed = storyteller.engine.help_embed(prefix)

    await ctx.reply(embed=embed)


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


# Initiative Management

@bot.group(invoke_without_command=True, name="mi", aliases=["minit"], case_insensitive=True)
@commands.guild_only()
async def initiative_manager(ctx, mod=None, *, args=None):
    """Displays the initiative table for the current channel."""
    response = storyteller.parse.initiative(ctx, mod, args)
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
async def initiative_remove_character(ctx, *, args=None):
    """Remove a character from initiative manager."""
    response = storyteller.parse.initiative_removal(ctx, args)
    await ctx.reply(content=response.content, embed=response.embed)

@initiative_manager.command(name="reroll")
@commands.guild_only()
async def initiative_reroll(ctx):
    """Rerolls all initiative and prints the new table."""
    manager = storyteller.initiative.get_table(ctx.channel.id)

    if manager:
        manager.reroll()
        await initiative_manager(ctx) # Print the new initiative table

        # Store the new initiatives
        characters = manager.characters
        for character in characters:
            init = characters[character]

            storyteller.initiative.set_initiative(
                ctx.channel.id, character, init.mod, init.die
            )
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

    # TEMPORARY
    channels = set(storyteller.initiative.all_tables.keys())
    for channel in channels:
        channel = await bot.fetch_channel(channel)
        guild = channel.guild
        print(f"Channel {channel.id} => Guild {guild.id} ({guild.name})")
        storyteller.initiative.temp_associate_guild(guild.id, channel.id)

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


# Misc

def __status_message():
    """Sets the bot's Discord presence message."""
    servers = len(bot.guilds)
    return f"!m help | {servers} chronicles"


# End definitions
bot.run(os.environ["TZIMISCE_TOKEN"])
