import discord
import re
import random

from tzimisce.RollDB import RollDB
from tzimisce.Pool import Pool
from tzimisce import PlainRoll

class Masquerade(discord.Client):
    def __init__(self):
        discord.Client.__init__(self)

        random.seed()

        # Set up the important regular expressions
        self.invoked = re.compile('^[!/]mw?')
        self.poolx = re.compile('[!/]m(?P<will>w)?\s+(?P<pool>\d+)\s*(?P<difficulty>\d+)?\s*(?P<auto>\d+)?(?P<specialty> [^#]+)?\s*(?:#\s*(?P<comment>.*))?$')
        self.tradx = re.compile('^[!/]mw? (?P<syntax>(?P<repeat>\d+)d(?P<die>\d+)(?:\+(?P<mod>\d+))?)(?:\s*#\s*(?P<comment>.*))?$')
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
            #embed = self.database.list_stored_rolls(message.author.mention)
            stored_rolls = self.database.stored_rolls(message.author.mention)
            if len(stored_rolls) == 0:
                await message.channel.send(message.author.mention + ', you have no stored rolls!')
            else:
                embed = self.__build_embed(message, 'Stored Rolls', 0x1f3446, '', stored_rolls)
                await message.channel.send(content=message.author.mention, embed=embed)

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

        # Title format: 'Rolling 6 dice, difficulty 5'
        title = str(pool)
        if pool > 1:
            title += ' dice'
        else:
            title += ' die' # For the grammar Naxi in me.
        title += ', difficulty ' + str(difficulty)

        # Sometimes, a roll may have auto-successes that can be canceled by 1s.
        autos = m.group('auto')
        autos = '0' if autos is None else autos

        # Optional arguments
        specialty  = m.group('specialty')
        comment    = m.group('comment')

        # Perform rolls, format them, and figure out how many successes we have
        results = Pool()
        results.roll(pool, difficulty, will, specialty is not None, autos)

        if autos != '0':
            title += ', +' + autos

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
            ('Rolls', ', '.join(results.formatted), True),
            ('Result', results.formatted_count(), True),
        ]

        if specialty is not None:
            fields.append(('Specialty', specialty, True))

        if comment is not None:
            fields.append(('Comment', comment))

        return self.__build_embed(message, title, color, '', fields)

    #
    # A "traditional" roll, such as 5d10+2.
    #
    def __traditional_roll(self, message):
        m = self.tradx.match(message.content)
        repeat  = int(m.group('repeat'))
        die     = int(m.group('die'))
        mod     = m.group('mod')
        comment = m.group('comment')

        title = 'Rolling {}'.format(m.group('syntax'))

        # Get the rolls and assemble the fields
        rolls = PlainRoll.roll(repeat, die)
        if mod is not None:
            rolls.append(int(mod))

        fields = [
            ('Rolls', '+'.join([str(roll) for roll in rolls]), True),
            ('Result', str(sum(rolls)), True)
        ]

        if comment is not None:
            fields.append(('Comment', comment, False))

        return self.__build_embed(message, title, 0x14a1a0, '', fields)

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
        embed.add_field(name="Add bonus successes", value="```!m 6 5 3```")
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

    def __build_embed(self, message, title, color, description, fields):
        embed = discord.Embed(title=title, colour=discord.Colour(color), description=description)
        embed.set_author(name=self.__get_author(message), icon_url=message.author.avatar_url)

        for field in fields:
            name = field[0]
            value = field[1]
            inline = False

            if len(field) == 3:
                inline = field[2]

            embed.add_field(name=name, value=value, inline=inline)

        return embed
