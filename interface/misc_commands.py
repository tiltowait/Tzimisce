"""misc_commands.py - A cog that has miscellaneous commands."""

from discord.commands import slash_command
from discord.ext import commands

import storyteller


class MiscCommands(commands.Cog):
    """Cog for miscellaneous commands."""

    @slash_command(name="help")
    async def __help(self, ctx):
        """Displays the basic syntax and a link to the full help file."""
        embed = storyteller.engine.help_embed("/mm syntax:")
        await ctx.respond(embed=embed)


    @slash_command()
    async def coinflip(self, ctx):
        """Flip a coin!"""
        coin = storyteller.roll.traditional.roll(1, 2)[0]
        if coin == 1:
            coin = "**Heads!**"
        else:
            coin = "**Tails!**"

        await ctx.respond(coin)


def setup(bot):
    """Setup the command interface."""
    bot.add_cog(MiscCommands(bot))
