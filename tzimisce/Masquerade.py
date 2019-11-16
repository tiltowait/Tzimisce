import discord
import re
import random
from tzimisce.RollDB import RollDB
from tzimisce.Pool import Pool

class Masquerade(discord.Client):
    def __init__(self):
        discord.Client.__init__(self)

        random.seed()

        # Set up the important regular expressions
        self.invoked = re.compile('^[!/]mw?')
        self.poolx = re.compile('[!/]m(?P<will>w)? (?P<pool>\d+)(?P<difficulty> \d+)?(?P<specialty> [^#]+)?\s*(?:#\s*(?P<comment>.*))?$')
        self.tradx = re.compile('^[!/]mw? (?P<repeat>\d+)d(?P<die>\d+)(?:\+(?P<mod>\d+))?(?:\s*#\s*(?P<comment>.*))?$')
        self.helpx = re.compile('^[!/]m help.*$')

        # Colors help show, at a glance, if a roll was successful
        self.exceptional_color = 0x00ff00
        self.success_color     = 0x14a1a0
        self.fail_color        = 0x777777
        self.botch_color       = 0xff0000

        # Database nonsense
        self.database = RollDB()
        self.sqrx = re.compile('^[!/]mw? \w+') # Start of a saved roll query
        self.disp = re.compile('^[!/]mw? \$\s*$') # Display all stored rolls

    #
    # Fires once we're logged in.
    #
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    #
    # The meat. Fires every time a message is received.
    #
    async def on_message(self, message):
        if message.author == self.user:
            return

        # Check if we're invoking the bot at all
        if not self.invoked.match(message.content):
            return

        # The author name is used in embeds. It can either be the nickname, if
        # set, or simply their username.
        author = self.__get_author(message)

        # Standard roll. Pool, difficulty, specialty.
        if self.poolx.match(message.content):
            embed = self.__pool_roll(message)#message.content, author, message.author.avatar_url)
            await message.channel.send(content=message.author.mention, embed=embed)

        # Traditional roll. 1d10+5, etc.
        elif self.tradx.match(message.content):
            embed = self.__traditional_roll(message)
            await message.channel.send(content=message.author.mention, embed=embed)

        # Print the help message.
        elif self.helpx.match(message.content):
            embed = self.__help()
            await message.channel.send(content=message.author.mention, embed=embed)

        # Stored roll shenanigans. Create, edit, delete.
        elif self.sqrx.match(message.content):
            msg = self.database.query_saved_rolls(message.author.mention, message.content)

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
                await message.channel.send(message.author.mention + ': ' + msg)

        # Display all of the user's stored rolls.
        elif self.disp.match(message.content):
            embed = self.database.list_stored_rolls(message.author.mention)
            if embed is None:
                await message.channel.send(message.author.mention + ', you have no stored rolls!')
            else:
                await message.channel.send(content=message.author.mention + ', you have the following rolls stored:', embed=embed)

        # No idea what the user is asking
        else:
            await message.channel.send('{0}: Come again?'.format(message.author.mention))

    #
    # A pool-based VtM roll. Returns the results in a pretty embed.
    # Does not check that difficulty is 1 or > 10.
    #
    def __pool_roll(self, message):
        m = self.poolx.match(message.content)
        will = m.group('will') is not None
        pool = int(m.group('pool'))

        if pool == 0:
          pool = 1 # Rather than mess about with errors, just fix the mistake

        # Difficulty must be between 2 and 10. If it isn't supplied, go with
        # the default value of 6.
        difficulty = m.group('difficulty')
        if difficulty is None:
            difficulty = 6
        elif int(difficulty) > 10:
            difficulty = 10
        elif int(difficulty) < 2:
            difficulty = 2
        else:
            difficulty = int(difficulty)

        # Optional arguments
        specialty  = m.group('specialty')
        comment    = m.group('comment')

        # Perform rolls, format them, and figure out how many successes we have
        results = Pool()
        results.roll(pool, difficulty, will, specialty is not None)

        # Title format: 'Rolling 6 dice, difficulty 5'
        title = str(pool)
        if pool > 1:
            title += ' dice'
        else:
            title += ' die' # For the grammar Naxi in me.
        title += ', difficulty ' + str(difficulty)

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

        embed = discord.Embed(title=title, colour=discord.Colour(color))
        embed.set_author(name=self.__get_author(message), icon_url=message.author.avatar_url)

        embed.add_field(name="Rolls", value=', '.join(results.formatted), inline=True)
        embed.add_field(name="Result", value=results.result_str, inline=True)
        if specialty is not None:
            embed.add_field(name="Specialty", value=specialty, inline=True)
        if comment is not None:
            embed.add_field(name="Comment", value=comment, inline=False)

        return embed

    #
    # A "traditional" roll, such as 5d10+2.
    #
    def __traditional_roll(self, message):
        m = self.tradx.match(message.content)
        repeat  = int(m.group('repeat'))
        die     = int(m.group('die'))
        mod     = m.group('mod')
        comment = m.group('comment')

        title = 'Rolling {0}d{1}'.format(repeat, die)

        rolls = [random.randint(1, die) for _ in range(repeat)]
        if mod is not None:
            title += '+' + mod
            rolls.append(int(mod))

        sum = 0
        for roll in rolls:
            sum += roll

        # Create an embed to return
        embed = discord.Embed(title=title, colour=discord.Colour(0x14a1a0))
        embed.set_author(name=self.__get_author(message), icon_url=message.author.avatar_url)

        embed.add_field(name="Rolls", value='+'.join([str(roll) for roll in rolls]), inline=True)
        embed.add_field(name="Result", value=str(sum), inline=True)
        if comment is not None:
            embed.add_field(name="Comment", value=comment, inline=False)

        return embed

    #
    # Return a handy help embed.
    #
    def __help(self):
        embed = discord.Embed(title="Example Usage", colour=discord.Colour(0x1f3446), description="A sampling of available commands.")

        embed.add_field(name="Pool 5, difficulty 6 (implied)", value="```!m 5```", inline=False)
        embed.add_field(name="Pool 5, difficulty 8", value="```!m 5 8```", inline=False)
        embed.add_field(name="Add a comment", value="```!m 5 8 # Comment!```", inline=False)
        embed.add_field(name="Add a specialty", value="```!m 8 4 Koldunism```", inline=False)
        embed.add_field(name="All together", value="```!m 8 4 Koldunism # Int + Occult```", inline=False)
        embed.add_field(name="Traditional roll", value="Useful for Initiative rolls and other things.```!m 1d10+5 # Comments work here, too```", inline=False)
        embed.add_field(name="Store a roll", value="Does not store willpower use or comments.\n```!m danubian = 8 3 Koldunism```", inline=False)
        embed.add_field(name="Use a stored roll", value="May also use with Willpower.\n```!m danubian```", inline=False)
        embed.add_field(name="Delete a stored roll", value="```!m danubian =```", inline=False)
        embed.add_field(name="List stored rolls", value="```!m $```", inline=False)

        return embed

    def __get_author(self, message):
        if message.author.nick is not None:
            return message.author.nick
        else:
            return message.author.name
