"""macro_commands.py - Macro-related commands"""

import discord
from discord.commands import slash_command, Option, SlashCommandGroup
from discord.ext import commands

import storyteller


class MacroCommands(commands.Cog):
    """A cog for macro commands."""

    macros = SlashCommandGroup("macros", "Macro commands.")

    @macros.command(name="list")
    async def macro_list(self, ctx):
        """List all your macros on this server."""
        await storyteller.engine.show_stored_rolls(ctx)


def setup(bot):
    """Set up the command interface."""
    bot.add_cog(MacroCommands(bot))
