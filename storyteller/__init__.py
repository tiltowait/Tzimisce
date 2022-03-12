"""Package storyteller. The user need only know about Masquerade, the client class."""

import re

import discord

from storyteller import engine
from storyteller import initiative
from storyteller import roll
from storyteller.databases import SettingsDB, InitiativeDB, StatisticsDB
from storyteller import probabilities
from storyteller import views

initiative = InitiativeDB()
settings = SettingsDB()


async def stringify_mentions(ctx, sentence):
    """Replace all raw mentions and channels with their plaintext names."""
    if not sentence:
        return None

    # Use a set to avoid redundant lookups
    if (matches := set(re.findall(r"<[@#]!?\d+>", sentence))):
        member_converter = discord.ext.commands.MemberConverter()
        channel_converter = discord.ext.commands.GuildChannelConverter()

        replacements = {}
        failed_lookups = 0

        for match in matches:
            if match in replacements:
                continue

            if "@" in match:
                # Member lookup
                try:
                    replacement = await member_converter.convert(ctx, match)
                    replacements[match] = "@" + replacement.display_name
                except discord.ext.commands.MemberNotFound:
                    pass
            else:
                # Channel lookup
                try:
                    replacement = await channel_converter.convert(ctx, match)
                    replacements[match] = "#" + replacement.name
                except discord.ext.commands.BadArgument:
                    pass

            # Realistically, there should be no failed lookups. If there are,
            # the user is probably trying to lock up the bot. Give them three
            # tries in case there's something weird going on before bailing.
            if not match in replacements:
                failed_lookups += 1
                if failed_lookups == 3:
                    break

        # Replace the items in the original string
        for (match, replacement) in replacements.items():
            sentence = sentence.replace(match, replacement)

    return " ".join(sentence.split())
