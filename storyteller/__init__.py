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


async def stringize_mentions(ctx, args):
    """Convert mentions inside a list of arguments into plain text."""
    if args is None:
        return

    converter = discord.ext.commands.MemberConverter()
    converted = []

    if isinstance(args, str):
        args = args.split()

    for arg in args:
        if re.match(r"<@!?\d+>", arg) is not None:
            try:
                member = await converter.convert(ctx, arg)
                converted.append("@" + member.display_name)
            except discord.ext.commands.MemberNotFound:
                converted.append(arg)
        else:
            converted.append(arg)

    return " ".join(converted)
