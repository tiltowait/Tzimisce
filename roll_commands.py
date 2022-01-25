"""roll_commands.py - Cog for roll commands and related."""

import discord

from discord.commands import slash_command, Option
from discord.ext import commands


class RollCommands(commands.Cog):
    """A simple cog that exposes the roll command interface."""

    GUILD_IDS = [758492110591885373]


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
        await ctx.respond(syntax)


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
        await ctx.respond(syntax)


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
        await ctx.respond(syntax)


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
        await ctx.respond(syntax)


def setup(bot):
    """Set up the command interface."""
    bot.add_cog(RollCommands(bot))
