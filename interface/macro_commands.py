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


    @macros.command()
    async def purge(self, ctx):
        """Remove all macros you have on this server."""
        macro_count, meta_count = storyteller.engine.macro_counts(ctx)
        prompt = "Are you sure you wish to delete your macros on this server?"

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

        if macro_count + meta_count > 0:
            prompt += f"{newline}{notice} will be deleted."
            confirmation = storyteller.views.Confirmation(discord.ButtonStyle.danger)
            await ctx.respond(prompt, view=confirmation, ephemeral=True)
            await confirmation.wait()

            if confirmation.confirmed:
                await storyteller.engine.delete_user_rolls(ctx)
        else:
            await ctx.respond("You have no macros on this server!", ephemeral=True)


def setup(bot):
    """Set up the command interface."""
    bot.add_cog(MacroCommands(bot))
