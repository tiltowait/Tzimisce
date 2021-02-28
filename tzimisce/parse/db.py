"""db.py - Determine whether the user is invoking the macro database."""

import re
import discord

from tzimisce import masquerade

__suggestx = re.compile(r"`.*`.*`(?P<suggestion>.*)`")

async def parse(ctx, command):
    """Inspects command for database queries and acts on them as necessary."""
    if command["syntax"][0].isalpha(): # Only macros start with alpha
        if ctx.channel.type is discord.ChannelType.private:
            await ctx.send("Sorry, you can't store macros in private DMs!")
            return

        query_result = masquerade.database.query_saved_rolls(
            guild=ctx.guild.id,
            userid=ctx.author.id,
            command=command
        )

        # Created, updated, or deleted a roll (or error)
        if isinstance(query_result, str):
            adding_reaction = False

            # Database offered macro suggestion
            if query_result[-2:] == "`?":
                # First, create the invocation
                will = command["will"] or ""
                compact = command["compact"] or ""
                invoke = f"/m{will}{compact}"

                # Next, get the suggestion
                suggestion = __suggestx.match(query_result).group("suggestion")

                # Next, substitute it from the original syntax
                split = command["syntax"].split()
                split[0] = suggestion
                new_syntax = " ".join(split)

                # Build the new command
                new_command = f"{invoke} {new_syntax}"

                # Replace!
                query_result = query_result.replace(suggestion, new_command)
                adding_reaction = True

            message = await ctx.message.reply(f"{query_result}")
            if adding_reaction:
                await message.add_reaction("👍")

            return

        return query_result
