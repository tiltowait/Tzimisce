"""The main Tzimisce dicebot class."""

import re
import random
from collections import defaultdict

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
        self.invoked = re.compile(
            r"^[!/]m(?P<compact>c)?(?P<will>w)?\s(?P<syntax>[^#]+)(?:#\s*(?P<comment>.*))?$"
        )
        self.poolx = re.compile(
            r"^(?P<pool>\d+)\s*(?P<difficulty>\d+)?\s*(?P<auto>\d+)?(?P<specialty> [^#]+)?$"
        )
        self.tradx = re.compile(
            r"^(?P<syntax>\d+(d\d+)?(\s*\+\s*(\d+|\d+d\d+))*)$"
        )

        # Colors help show, at a glance, if a roll was successful
        self.exceptional_color = 0x00FF00
        self.success_color = 0x14A1A0
        self.fail_color = 0x777777
        self.botch_color = 0xFF0000

        # Database stuff
        self.database = RollDB()
        self.sqrx = re.compile(r"^[!/]mc?w? [\w-]+")  # Start of a saved roll query

    def __status_message(self):
        """Sets the bot's Discord presence message."""
        servers = len(self.guilds)
        return f"/m help | {servers} chronicles"

    # Various bookkeeping methods

    async def on_ready(self):
        """Print a message letting us know the bot logged in to Discord."""
        print(f"Logged on as {self.user}!")
        print(discord.version_info)

        await self.change_presence(activity=discord.Game(self.__status_message()))

    async def on_guild_join(self, guild):
        """When joining a guild, log it for statistics purposes."""
        print(f"Joining {guild}")
        self.database.add_guild(guild.id, guild.name)
        await self.change_presence(activity=discord.Game(self.__status_message()))

    async def on_guild_remove(self, guild):
        """We don't want to keep track of guilds we no longer belong to."""
        print(f"Removing {guild}")
        self.database.remove_guild(guild.id)
        await self.change_presence(activity=discord.Game(self.__status_message()))

    async def on_guild_update(self, before, after):
        """Sometimes guilds are renamed. Fix that."""
        print(f"Renaming {before} to {after}")
        self.database.rename_guild(after.id, after.name)

    # Main handler

    async def on_message(self, message):
        """Parse every message and determine if action is needed."""
        if message.author == self.user:
            return

        # Check if we're invoking the bot at all
        match = self.invoked.match(message.content)
        if not match:
            return

        # The COMMAND dict contains info on compact mode, willpower, comment,
        # and the command syntax. At this poitn, the syntax is unvalidated and
        # may be in error. Validators below determine if syntax is actionable
        # or display an error message.

        command = defaultdict(lambda: None) # Avoid testing optional components
        command.update(match.groupdict())
        command["syntax"] = command["syntax"].strip()

        # Discord will reject messages that are too long
        if command["comment"] and len(command["comment"]) > 500:
            reduction = len(command["comment"]) - 500
            characters = "character"
            if reduction > 1: # Because I can't risk improper pluralization
                characters += "s"

            await message.channel.send(
                f"{message.author.mention}: Comment too long by {reduction} {characters}."
            )
            return

        # Check if the user is invoking the help command
        if command["syntax"] == "help":
            embed = self.__help()
            await message.channel.send(content=message.author.mention, embed=embed)
            return

        # Coin flip
        if command["syntax"] == "coin":
            coin = random.randint(1, 2)
            if coin == 1:
                coin = "Heads!"
            else:
                coin = "Tails!"

            await message.channel.send(f"{message.author.mention}: {coin}")
            return

        # If the command involves the RollDB, we need to modify the syntax first
        if command["syntax"][0].isalpha(): # No valid roll starts with alpha
            query_result = self.database.query_saved_rolls(
                guild=message.guild.id,
                userid=message.author.id,
                command=command
            )

            # Created, updated, or deleted a roll (or error)
            if isinstance(query_result, str):
                await message.channel.send(f"{message.author.mention}: {query_result}")
                return

            # Retrieved a roll
            command = query_result

        # Pooled roll
        pool = self.poolx.match(command["syntax"])
        if pool:
            command.update(pool.groupdict())
            send = self.__pool_roll(message.author, command)

            if isinstance(send, discord.Embed):
                await message.channel.send(content=message.author.mention, embed=send)
            else: # It's a string
                await message.channel.send(send)

            self.database.increment_rolls(message.guild.id)
            return

        # Traditional roll (e.g. 2d10+4)
        traditional = self.tradx.match(command["syntax"])
        if traditional:
            command.update(traditional.groupdict())
            try:
                send = self.__traditional_roll(message.author, command)
                if isinstance(send, discord.Embed):
                    await message.channel.send(content=message.author.mention, embed=send)
                else:
                    await message.channel.send(send)

                self.database.increment_rolls(message.guild.id)
            except ValueError as error:
                await message.channel.send(f"{message.author.mention}: {str(error)}")

            return

        # Display all of the user's stored rolls.
        if command["syntax"] == "$":
            stored_rolls = self.database.stored_rolls(message.guild.id, message.author.id)
            if len(stored_rolls) == 0:
                await message.channel.send(
                    f"{message.author.mention}, you have no stored rolls!"
                )
            else:
                embed = self.__build_embed(
                    author=message.author,
                    title="Stored Rolls",
                    color=0x1F3446,
                    fields=stored_rolls,
                )
                await message.channel.send(content=message.author.mention, embed=embed)

            return # Unnecessary, but here in case we add more cases in future

    def __pool_roll(self, author, command):
        """
        A pool-based VtM roll. Returns the results in a pretty embed.
        Does not check that difficulty is 1 or > 10.
        """
        will = command["will"]
        compact = command["compact"]
        pool = int(command["pool"])

        if pool == 0:
            pool = 1  # Rather than mess about with errors, just fix the mistake

        if pool > 100:
            return f"{author.mention}: Error! Pools cannot be larger than 100."

        # Difficulty must be between 2 and 10. If it isn't supplied, go with
        # the default value of 6.
        difficulty = command["difficulty"]
        if not difficulty:
            difficulty = 6
        else:
            difficulty = int(difficulty)
            if difficulty > 10:
                difficulty = 10
            elif difficulty < 2:
                difficulty = 2

        # Title format: 'Pool X, difficulty Y'
        title = f"Pool {pool}, diff. {difficulty}"

        # Sometimes, a roll may have auto-successes that can be canceled by 1s.
        autos = command["auto"]
        if autos:
            autos = int(autos)
            title += f", +{pluralize_autos(autos)}"
        else:
            autos = 0

        specialty = command["specialty"] # Doubles 10s if set

        # Perform rolls, format them, and figure out how many successes we have
        results = Pool()
        results.roll(pool, difficulty, will, specialty is not None, autos)

        comment = command["comment"]

        # Compact formatting
        if compact:
            results_string = results.formatted_count()

            compact_string = f"{results.formatted} = **{results_string}**"
            if comment:
                compact_string += f"\n> {comment}"

            if specialty:
                compact_string += f"\n> ***{specialty}***"

            return f"{author.mention}\n{compact_string}"

        # If not compact, put the results into an embed

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
        fields = [("Dice", results.formatted, True)]

        if specialty:
            fields.append(("Specialty", specialty, True))

        fields.append(("Result", results.formatted_count(), False))

        return self.__build_embed(
            author=author, header=title, color=color, fields=fields,
            footer=comment
        )

    def __traditional_roll(self, author, command):
        """A "traditional" roll, such as 5d10+2."""
        compact = command["compact"]
        syntax = command["syntax"]
        comment = command["comment"]
        description = None # Used to show individual dice results

        # Get the rolls and assemble the fields
        rolls = PlainRoll.roll_string(syntax)
        result = str(sum(rolls))

        # Show the individual dice if more than 1 were rolled
        if len(rolls) > 1:
            description = "+".join([str(roll) for roll in rolls])

        # Compact mode means no embed
        if compact:
            compact_string = ""
            if description:
                compact_string = f"{description} ="

            compact_string = f"{compact_string} {result}"
            if comment:
                compact_string += f"\n> {comment}"

            return f"{author.mention}\n{compact_string}"

        # Not using compact mode!
        fields = [("Result", result, False),]

        embed = self.__build_embed(
            author=author, header=syntax, color=0x000000, fields=fields,
            footer=comment, description=description
        )

        return embed

    def __help(self):
        """Return a handy help embed."""
        embed=discord.Embed(title="[Tzimisce] | Help", url="https://tiltowait.github.io/Tzimisce/", description="Click above for a complete listing of commands, including macros (roll saving) and more.")
        embed.add_field(name="Basic Syntax", value="```/m <pool> [difficulty] [specialty] # comment```Difficulty, specialty, and comment are all optional.", inline=False)
        embed.add_field(name="Example", value="```/m 8 7 Domineering # Command```", inline=False)

        return embed

    def __build_embed(
        self, fields, author=None, title="", color=0x1F3446, description="",
        header=None, footer=None
    ):
        """Return a discord embed with a variable number of fields."""
        embed = discord.Embed(
            title=title, colour=discord.Colour(color), description=description
        )

        if footer:
            embed.set_footer(text=footer)

        if author:
            avatar = author.avatar_url
            author = author.display_name

            if header:
                author += f": {header}"

            embed.set_author(name=author, icon_url=avatar)

        for field in fields:
            name = field[0]
            value = field[1]
            inline = False

            if len(field) == 3:
                inline = field[2]

            embed.add_field(name=name, value=value, inline=inline)

        return embed

def pluralize_autos(autos):
    string = f"{autos} auto"
    if autos > 1:
        string += "s"

    return string
