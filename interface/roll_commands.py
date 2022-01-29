"""roll_commands.py - Cog for roll commands and related."""

# pylint: disable=invalid-name

from collections import defaultdict

import discord
from discord.commands import slash_command, Option
from discord.ext import commands

import storyteller


class RollCommands(commands.Cog):
    """A simple cog that exposes the roll command interface."""

    async def _roll(self, ctx, syntax: str, *options):
        """Perform a roll."""

        # Split the comment from the syntax
        content = " ".join(syntax.split())
        content = content.split("#", 1)

        syntax = content.pop(0)
        comment = content[0] if content else None

        if not syntax:
            raise IndexError

        command = defaultdict(lambda: None)
        command["syntax"] = " ".join(syntax.split())
        command["comment"] = " ".join(comment.split()) if comment else None

        guild_settings = storyteller.settings.settings_for_guild(ctx.guild)
        command.update(guild_settings)

        # See what options the user has selected, if any. These options are all
        # very terse due to artifacts from the old command structure. A proper
        # rewrite would be more elegant.

        if "w" in options:
            command["will"] = "w"
        if "c" in options or guild_settings["use_compact"]:
            command["use_compact"] = "c"
            if ctx.guild:
                storyteller.engine.statistics.increment_compact_rolls(ctx.guild)
        if "z" in options:
            command["never_botch"] = "z"

        # If the bot doesn't have embed permissions, then we don't want to count that in the stats
        # Disabling until library fix/workaround is found
        perms = ctx.channel.permissions_for(ctx.me)
        print(perms)
        print(dir(perms))
        print("Embed?", perms.embed_links)
        #if not ctx.channel.permissions_for(ctx.me).embed_links:
            #command["use_compact"] = "c"

        await storyteller.engine.handle_command(command, ctx)


    @slash_command()
    async def mm(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice."""
        await self._roll(ctx, syntax)


    @slash_command()
    async def cmm(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice using compact mode."""
        await self._roll(ctx, syntax, "c")


    @slash_command()
    async def mw(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice, adding Willpower."""
        await self._roll(ctx, syntax, "w")


    @slash_command()
    async def cmw(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice using compact mode, adding Willpower."""
        await self._roll(ctx, syntax, "c", "w")


    # "Zero Botch" commands

    @slash_command()
    async def zmm(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice. Botches are simple failures."""
        await self._roll(ctx, syntax, "z")


    @slash_command()
    async def zmw(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice, adding Willpower. Botches are simple failures."""
        await self._roll(ctx, syntax, "z", "w")


    @slash_command()
    async def czmm(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice using compact mode. Botches are simple failures."""
        await self._roll(ctx, syntax, "c", "z")


    @slash_command()
    async def czmw(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL [DIFF] [AUTOS] [SPEC] [# Comment] Everything in brackets is optional"
        ),
    ):
        """Roll the dice using compact mode and adding Willpower. Botches are simple failures."""
        await self._roll(ctx, syntax, "c", "z", "w")


    @slash_command()
    async def chance(self, ctx):
        """Roll a chance die (primarily for CofD games)."""
        command = defaultdict(lambda: False)
        command.update(storyteller.settings.settings_for_guild(ctx.guild))

        # A chance roll is 1d10, and you may only succeed on a 10. A 1 is a critical failure. We need to
        # override some/most server settings to make sure the roll is done correctly. As of now, the
        # only thing we're keeping is †he compact mode flag; however, additional settings may be added
        # in the future, so the framework is laid now.
        command["syntax"] = "1 10"
        command["comment"] = "Chance roll. Succeed on 10, botch on 1. Is today your lucky day?"
        command["chronicles"] = False # Have to override this, because a chance roll is closer to WoD
        command["xpl_always"] = False
        command["never_botch"] = False

        await storyteller.engine.handle_command(command, ctx)


def setup(bot):
    """Set up the command interface."""
    bot.add_cog(RollCommands(bot))
