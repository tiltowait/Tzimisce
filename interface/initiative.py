"""initiative.py - Cog for managing initiative."""
# pylint: disable=invalid-name

import re

import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands

import storyteller


class InitiativeCommands(commands.Cog):
    """A cog for initiative commands."""

    init = SlashCommandGroup("init", "Initiative Manager")

    @init.command()
    @commands.guild_only()
    async def show(self, ctx: discord.ApplicationContext):
        """Show the current channel's initiative table."""
        await ctx.defer()
        try:
            response = _init_parse(ctx)
            await ctx.respond(content=response.content, embed=response.embed)
        except ValueError as err:
            await ctx.respond(str(err))

    @init.command()
    @commands.guild_only()
    async def add(
        self,
        ctx: discord.ApplicationContext,
        mod: Option(str, "The initiative modifier"),
        character: Option(str, "The character who's acting", required=False),
    ):
        """Add a character to the initiative table."""
        await ctx.defer()
        try:
            args = mod.split()
            mod = args.pop(0)
            int(mod)

            if character is None:
                if args:
                    character = " ".join(args)
                else:
                    character = ""

            character = await storyteller.stringify_mentions(ctx, character)

            response = _init_parse(ctx, mod, character)
            await ctx.respond(content=response.content, embed=response.embed)
        except ValueError:
            await ctx.respond(
                "**Error:** `mod` must be a number. Use `character` parameter to add a character.",
                ephemeral=True,
            )

    @init.command()
    @commands.guild_only()
    async def bulk(
        self, ctx: discord.ApplicationContext, characters: Option(str, "Name1=Mod1 Name2=Mod2 ...")
    ):
        """Add multiple characters to the initiative table."""
        await ctx.defer()
        characters = re.sub(r"\s*=\s*", r"=", characters)

        try:
            chars_and_mods = []
            char_names = []
            chars = characters.split()
            for char in chars:
                char, mod = char.split("=")
                mod = int(mod)

                chars_and_mods.append((char, mod))
                char_names.append(char)

            storyteller.parse.initiative_bulk_add(ctx, chars_and_mods)

            last = char_names.pop(-1)
            if (num_chars := len(char_names)) == 0:
                char_str = last
            elif num_chars == 1:
                char_str = f"{char_names[0]} and {last}"
            else:
                char_str = ", ".join(char_names)
                char_str += f", and {last}"

            await ctx.respond(f"Added {char_str} to the initiative table.")
        except:
            await ctx.respond(
                "Error: Expected `Name1=Mod1 Name2=Mod2 ...`. Mods must be numbers!", ephemeral=True
            )

    @init.command()
    @commands.guild_only()
    async def rm(self, ctx, character: Option(str, "The character to remove", default="")):
        """Remove a character from the channel's initiative table."""
        await ctx.defer()
        try:
            response = storyteller.parse.initiative_removal(ctx, character)
            await ctx.respond(content=response.content, embed=response.embed)
        except ValueError as err:
            await ctx.respond(err, ephemeral=True)

    @init.command()
    @commands.guild_only()
    async def reroll(self, ctx):
        """Re-roll this channel's initiative."""
        await ctx.defer()
        manager = storyteller.initiative.get_table(ctx.channel.id)

        if manager:
            # Reroll and store the new initiatives before displaying
            manager.reroll()

            for character, init in manager.characters.items():
                storyteller.initiative.set_initiative(
                    ctx.guild.id, ctx.channel.id, character, init.mod, init.die
                )

            response = _init_parse(ctx, reroll=True)  # Print the new initiative table
            await ctx.respond(content=response.content, embed=response.embed)
        else:
            await ctx.respond("Initiative isn't set for this channel!", ephemeral=True)

    @init.command()
    @commands.guild_only()
    async def dec(
        self,
        ctx,
        declaration: Option(str, "Format: <action> [-n character] [-c N]"),
    ):
        """Declare an initiative action."""
        await ctx.defer()
        try:
            character = storyteller.parse.initiative_declare(ctx, declaration.split())
            await ctx.respond(f"Declared {character}'s action!")
        except SyntaxError as error:
            await ctx.respond(error, ephemeral=True)

    @init.command()
    @commands.guild_only()
    async def clear(self, ctx):
        """Clear this channel's initiative table."""
        await ctx.defer()
        try:
            storyteller.initiative.remove_table(ctx.channel.id)
            await ctx.respond("Reset initiative in this channel!")
        except KeyError:
            await ctx.respond("This channel's initiative table is already empty!", ephemeral=True)


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(InitiativeCommands(bot))


def _init_parse(ctx, mod=None, character=None, reroll=False):
    """Helper method that handles basic initiative stuff."""
    use_embed = _use_embed(ctx.guild.id)
    return storyteller.parse.initiative(ctx, mod, character, reroll, use_embed)


def _use_embed(guildid: int) -> bool:
    """
    Determine whether a command should use compact mode.
    Args:
        guildid (int): The Discord ID of the guild where the bot was invoked
    Returns (bool): True if the bot should use compact mode
    """
    guild_settings = storyteller.settings.settings_for_guild(guildid)
    return not guild_settings["use_compact"]
