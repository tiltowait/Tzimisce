"""roll_commands.py - Cog for roll commands and related."""

from collections import defaultdict

import discord

from discord.commands import slash_command, Option
from discord.ext import commands

import storyteller


class RollCommands(commands.Cog):
    """A simple cog that exposes the roll command interface."""

    GUILD_IDS = [758492110591885373]


    async def _roll(self, ctx, syntax: str, *options):
        """Perform a roll."""

        # Split the comment from the syntax
        content = " ".join(syntax.split())
        content = content.split("#", 1)

        syntax = content.pop(0)
        comment = content or None

        if not syntax:
            raise IndexError

        command = defaultdict(lambda: None)
        command["syntax"] = " ".join(syntax.split())
        command["comment"] = " ".join(comment.split()) if comment else None

        guild_settings = storyteller.settings.settings_for_guild(ctx.guild)
        command.update(guild_settings)

        # See what options the user has selected, if any
        if "w" in options:
            command["will"] = "w"
        if "c" in options or guild_settings["use_compact"]:
            command["use_compact"] = "c"
            if ctx.guild:
                storyteller.engine.statistics.increment_compact_rolls(ctx.guild)
        if "z" in options:
            command["never_botch"] = "z"

        # If the bot doesn't have embed permissions, then we don't want to count that in the stats
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            command["use_compact"] = "c"

        await storyteller.engine.handle_command(command, ctx)


    @slash_command(guild_ids=GUILD_IDS)
    async def roll(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        )
    ):
        """Roll the dice."""
        await self._roll(ctx, syntax)



    @slash_command(guild_ids=GUILD_IDS)
    async def croll(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        )
    ):
        """Roll the dice using compact mode."""
        await self._roll(ctx, syntax, "c")


    @slash_command(guild_ids=GUILD_IDS)
    async def wroll(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        )
    ):
        """Roll the dice, adding Willpower."""
        await self._roll(ctx, syntax, "w")


    @slash_command(guild_ids=GUILD_IDS)
    async def cwroll(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        )
    ):
        """Roll the dice using compact mode, adding Willpower."""
        await self._roll(ctx, syntax, "c", "w")


def setup(bot):
    """Set up the command interface."""
    bot.add_cog(RollCommands(bot))
