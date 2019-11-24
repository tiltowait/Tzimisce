"""The main Tzimisce dicebot class."""

import re
import random

import discord
from tzimisce.RollDB import RollDB
from tzimisce.Pool import Pool
from tzimisce import PlainRoll


class Masquerade(discord.Client):
    """The Discord bot parses messages to see if it needs to perform a roll."""

    # pylint: disable=too-many-instance-attributes
    # We need all of them.

    def __init__(self):
        discord.Client.__init__(self)

        random.seed()

        # Set up the important regular expressions
        self.invoked = re.compile(r"^[!/]mw?")
        self.poolx = re.compile(
            r"[!/]m(?P<will>w)?\s+(?P<pool>\d+)\s*(?P<difficulty>\d+)?\s*(?P<auto>\d+)?(?P<specialty> [^#]+)?\s*(?:#\s*(?P<comment>.*))?$"
        )
        self.tradx = re.compile(
            r"^[!/]mw? (?P<syntax>\d+(d\d+)?(\s*\+\s*(\d+|\d+d\d+))*)\s*(?:#\s*(?P<comment>.*))?$"
        )
        self.helpx = re.compile(r"^[!/]m help.*$")

        # Colors help show, at a glance, if a roll was successful
        self.exceptional_color = 0x00FF00
        self.success_color = 0x14A1A0
        self.fail_color = 0x777777
        self.botch_color = 0xFF0000

        # Database nonsense
        self.database = RollDB()
        self.sqrx = re.compile(r"^[!/]mw? \w+")  # Start of a saved roll query
        self.disp = re.compile(r"^[!/]mw? \$\s*$")  # Display all stored rolls

    async def on_ready(self):
        """Print a message letting us know the bot logged in to Discord."""
        print(f"Logged on as {self.user}!")

    async def on_guild_join(self, guild):
        """When joining a guild, log it for statistics purposes."""
        print(f"Joining {guild}")
        self.database.add_guild(guild.id, guild.name)

    async def on_guild_remove(self, guild):
        """We don't want to keep track of guilds we no longer belong to."""
        print(f"Removing {guild}")
        self.database.remove_guild(guild.id)

    async def on_guild_update(self, before, after):
        """Sometimes guilds are renamed. Fix that."""
        print(f"Renaming {before} to {after}")
        self.database.rename_guild(after.id, after.name)

    async def on_message(self, message):
        """Fires every time a message is received. Parses it to see if a roll is needed."""
        if message.author == self.user:
            return

        # Check if we're invoking the bot at all
        if not self.invoked.match(message.content):
            return

        # Standard roll. Pool, difficulty, specialty.
        if self.poolx.match(message.content):
            embed = self.__pool_roll(message)
            await message.channel.send(content=message.author.mention, embed=embed)

        # Traditional roll. 1d10+5, etc.
        elif self.tradx.match(message.content):
            try:
                embed = self.__traditional_roll(message)
                await message.channel.send(content=message.author.mention, embed=embed)
            except ValueError as error:
                await message.channel.send(f"{message.author.mention}: {str(error)}")

        # Print the help message.
        elif self.helpx.match(message.content):
            embed = self.__help()
            await message.channel.send(content=message.author.mention, embed=embed)

        # Stored roll shenanigans. Create, edit, delete.
        elif self.sqrx.match(message.content):
            msg = self.database.query_saved_rolls(message.author.id, message.content)

            # If the user has retrieved a roll, go ahead and roll it.
            if self.poolx.match(msg):
                message.content = msg
                embed = self.__pool_roll(message)
                await message.channel.send(content=message.author.mention, embed=embed)

            elif self.tradx.match(msg):
                message.content = msg
                embed = self.__traditional_roll(message)
                await message.channel.send(content=message.author.mention, embed=embed)

            # Created, deleted, or updated a roll.
            else:
                await message.channel.send(f"{message.author.mention}: {msg}")

        # Display all of the user's stored rolls.
        elif self.disp.match(message.content):
            stored_rolls = self.database.stored_rolls(message.author.id)
            if len(stored_rolls) == 0:
                await message.channel.send(
                    f"{message.author.mention}, you have no stored rolls!"
                )
            else:
                embed = self.__build_embed(
                    message=message,
                    title="Stored Rolls",
                    color=0x1F3446,
                    fields=stored_rolls,
                )
                await message.channel.send(content=message.author.mention, embed=embed)

        # No idea what the user is asking
        else:
            await message.channel.send(f"{message.author.mention}: Come again?")

    def __pool_roll(self, message):
        """
        A pool-based VtM roll. Returns the results in a pretty embed.
        Does not check that difficulty is 1 or > 10.
        """
        match = self.poolx.match(message.content)
        will = match.group("will") is not None
        pool = int(match.group("pool"))

        if pool == 0:
            pool = 1  # Rather than mess about with errors, just fix the mistake

        # Difficulty must be between 2 and 10. If it isn't supplied, go with
        # the default value of 6.
        difficulty = match.group("difficulty")
        if not difficulty:
            difficulty = 6
        elif int(difficulty) > 10:
            difficulty = 10
        elif int(difficulty) < 2:
            difficulty = 2
        else:
            difficulty = int(difficulty)

        # Title format: 'Rolling 6 dice, difficulty 5'
        title = str(pool)
        if pool > 1:
            title += " dice"
        else:
            title += " die"  # For the grammar Nazi in me.
        title += f", difficulty {difficulty}"

        # Sometimes, a roll may have auto-successes that can be canceled by 1s.
        autos = match.group("auto")
        if autos:
            title += f", +{autos}"
        else:
            autos = "0"

        specialty = match.group("specialty")  # Doubles 10s if set

        # Perform rolls, format them, and figure out how many successes we have
        results = Pool()
        results.roll(pool, difficulty, will, specialty is not None, autos)

        # Put the results into an embed

        # The embed's color indicates if the roll succeeded, failed, or botched
        color = 0
        if results.successes >= 5:
            color = self.exceptional_color
        elif results.successes > 0:
            color = self.success_color
        elif results.successes < 0:
            color = self.botch_color
        else:
            color = self.fail_color

        # Set up the embed fields
        fields = [
            ("Rolls", ", ".join(results.formatted), True),
            ("Result", results.formatted_count(), True),
        ]

        if specialty:
            fields.append(("Specialty", specialty, True))

        comment = match.group("comment")
        if comment:
            fields.append(("Comment", comment))

        return self.__build_embed(
            message=message, title=title, color=color, fields=fields
        )

    def __traditional_roll(self, message):
        """A "traditional" roll, such as 5d10+2."""
        match = self.tradx.match(message.content)
        syntax = match.group("syntax")
        comment = match.group("comment")

        title = f"Rolling {syntax}"

        # Get the rolls and assemble the fields
        rolls = PlainRoll.roll_string(syntax)

        fields = [
            ("Rolls", "+".join([str(roll) for roll in rolls]), True),
            ("Result", str(sum(rolls)), True),
        ]

        if comment:
            fields.append(("Comment", comment, False))

        return self.__build_embed(
            message=message, title=title, color=0x14A1A0, fields=fields
        )

    def __help(self):
        """Return a handy help embed."""
        fields = [
            ("Pool 5, difficulty 6 (implied)", "```!m 5```"),
            ("Pool 5, difficulty 8", "```!m 5 8```"),
            ("Add a comment", "```!m 5 8 # Comment!```"),
            ("Add a specialty", "```!m 8 4 Koldunism```"),
            ("All together", "```!m 8 4 Koldunism # Int + Occult```"),
            ("Add bonus successes", "```!m 6 5 3```"),
            (
                "Traditional roll",
                "Useful for Initiative rolls and other things.```!m 1d10+5```",
            ),
            (
                "Store a roll",
                "Ignores willpower and comments.\n```!m danubian = 8 3 Koldunism```",
            ),
            ("Use a stored roll", "May also use with Willpower.\n```!m danubian```"),
            ("Delete a stored roll", "```!m danubian =```"),
            ("List stored rolls", "```!m $```"),
        ]

        return self.__build_embed(
            title="Example Usage",
            description="A sampling of available commands",
            fields=fields,
        )

    def __build_embed(
        self, fields, message=None, title="", color=0x1F3446, description=""
    ):
        """Return a discord embed with a variable number of fields."""
        embed = discord.Embed(
            title=title, colour=discord.Colour(color), description=description
        )

        if message:
            author = message.author.nick
            if not author:
                author = message.author.name

            embed.set_author(name=author, icon_url=message.author.avatar_url)

        for field in fields:
            name = field[0]
            value = field[1]
            inline = False

            if len(field) == 3:
                inline = field[2]

            embed.add_field(name=name, value=value, inline=inline)

        return embed
