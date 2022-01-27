"""settings.py - Guild settings cog."""

from discord.commands import SlashCommandGroup, Option
from discord.ext import commands

import storyteller


class SettingsCommands(commands.Cog):
    """A cog for guild settings commands."""

    settings = SlashCommandGroup("settings", "Server settings management.")

    @settings.command()
    @commands.guild_only()
    async def view(self, ctx):
        """View the server's settings."""
        prefix = storyteller.settings.get_prefixes(ctx.guild.id)[0]
        msg = []
        for param in storyteller.settings.available_parameters:
            value = storyteller.settings.value(ctx.guild.id, param)
            msg.append(f"**{param}**: `{value}`")
        msg = "\n".join(msg)
        details = f"For more info or to set: `{prefix} settings <parameter> [value]`"

        await ctx.respond(f"This server's settings:\n{msg}\n{details}")


    @settings.command()
    @commands.guild_only()
    async def info(
        self,
        ctx,
        key: Option(str, "The key to inspect", choices=storyteller.settings.available_parameters)
    ):
        """Display detailed information on a server parameter."""
        value = storyteller.settings.value(ctx.guild.id, key)
        info = storyteller.settings.parameter_information(key)
        await ctx.respond(f"{info} (Current: `{value}`)")


    @settings.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set(
        self,
        ctx,
        key: Option(
            str,
            "The parameter to change",
            choices=storyteller.settings.available_parameters
        ),
        value: Option(str, "The new setting. True/False for most, but some take a number")
    ):
        """Change a server setting."""
        if key == storyteller.settings.PREFIX and value == "reset":
            value = None

        try:
            message = storyteller.settings.update(ctx.guild.id, key, value)
            await ctx.respond(message)
        except ValueError as err:
            await ctx.respond(err, ephemeral=True)


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(SettingsCommands(bot))
