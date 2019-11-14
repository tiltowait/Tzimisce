import discord
import re
import random
import os
import psycopg2
from hashlib import sha3_384

DATABASE_URL = os.environ['DATABASE_URL']

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
        self.success_color = 0x14a1a0
        self.fail_color    = 0x070707
        self.botch_color   = 0xff0000

        # Database stuff

        # Set up the database connection
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS SavedRolls
                              (ID     Text NOT NULL,
                               Name   Text NOT NULL,
                               Syntax Text NOT NULL);''')
        self.conn.commit()

        # Basic regex for manipulating stored rolls
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
        if message.author == client.user:
            return

        # Check if we're invoking the bot at all
        if not self.invoked.match(message.content):
            return

        # The author name is used in embeds. It can either be the nickname, if
        # set, or simply their username.
        author = ''
        if message.author.nick is not None:
            author = message.author.nick
        else:
            author = message.author.name

        # Standard roll. Pool, difficulty, specialty.
        if self.poolx.match(message.content):
            embed = self.__pool_roll(message.content, author, message.author.avatar_url)
            await message.channel.send(content=message.author.mention, embed=embed)

        # Traditional roll. 1d10+5, etc.
        elif self.tradx.match(message.content):
            embed = self.__traditional_roll(message.content, author, message.author.avatar_url)
            await message.channel.send(content=message.author.mention, embed=embed)

        # Print the help message.
        elif self.helpx.match(message.content):
            embed = self.__help()
            await message.channel.send(content=message.author.mention, embed=embed)

        # Stored roll shenanigans. Create, edit, delete.
        elif self.sqrx.match(message.content):
            msg = self.__query_saved_rolls(message.author.mention, message.content)

            # If the user has retrieved a roll, go ahead and roll it.
            if self.poolx.match(msg):
                embed = self.__pool_roll(msg, author, message.author.avatar_url)
                await message.channel.send(content=message.author.mention, embed=embed)

            elif self.tradx.match(msg):
                embed = self.__traditional_roll(msg, author, message.author.avatar_url)
                await message.channel.send(content=message.author.mention, embed=embed)

            # Created, deleted, or updated a roll.
            else:
                await message.channel.send(message.author.mention + ': ' + msg)

        # Display all of the user's stored rolls.
        elif self.disp.match(message.content):
            embed = self.__list_stored_rolls(message.author.mention)
            if embed is None:
                await message.channel.send(message.author.mention + ', you have no stored rolls!')
            else:
                await message.channel.send(content=message.author.mention + ', you have the following rolls stored:', embed=embed)

        # No idea what the user is asking
        else:
            await message.channel.send('{0}: Come again?'.format(message.author.mention))

    #
    # Roll a specific die a number of times and return the results as an array.
    #
    def __roll(self, repeat, die):
        repeat = int(repeat)
        return sorted([random.randint(1,die) for _ in range(repeat)], reverse=True)

    #
    # Use Markdown formatting on the rolls.
    #   Cross out failures.
    #   Bold and cross out ones.
    #   Bold tens if a specialty is in use.
    #
    def __format_rolls(self, rolls, difficulty, spec):
        formatted = []
        for roll in rolls:
            if roll == 1:
                formatted.append('~~**{0}**~~'.format(roll))
            elif roll < difficulty:
                formatted.append('~~{0}~~'.format(roll))
            elif roll == 10 and spec:
                formatted.append('**{0}**'.format(roll))
            else:
                formatted.append('{0}'.format(roll))

        return formatted

    #
    # Sums the number of successes, taking into account Willpower use.
    #   Botch if no successes or willpower and failures > 0
    #   Failure if ones > successes
    #   Success if successes > ones
    #
    def __count_successes(self, rolls, difficulty, wp, spec):
        suxx  = 0
        fails = 0

        for roll in rolls:
            if roll >= difficulty:
                suxx += 1
                if roll == 10 and spec:
                    suxx += 1
            elif roll == 1:
                fails += 1

        # Three possible results:
        #   * Botch
        #   * Failure
        #   # Success
        # If using Willpower, there's always one guaranteed success.
        if not wp and fails > 0 and suxx == 0: # Botch
            return 'Botch: {0}'.format(-fails)
        else:
            suxx = suxx - fails
            suxx = 0 if suxx < 0 else suxx
            if wp:
                suxx += 1

            if suxx == 0:
                return 'Failure'
            else:
                output = '{0} success'.format(suxx)
                if suxx > 1:
                  output += 'es' # Properly pluralize!

                if wp:
                  output += ' (inc WP)'

                return output

    #
    # A pool-based VtM roll. Returns the results in a pretty embed.
    # Does not check that difficulty is 1 or > 10.
    #
    def __pool_roll(self, message, author, avatar):
        m = self.poolx.match(message)
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
        rolls = self.__roll(pool, 10)
        formatted = self.__format_rolls(rolls, difficulty, specialty is not None)
        successes = self.__count_successes(rolls, difficulty, will, specialty is not None)

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
        if "success" in successes:
            color = self.success_color
        elif "Botch" in successes:
            color = self.botch_color
        else:
            color = self.fail_color

        embed = discord.Embed(title=title, colour=discord.Colour(color))
        embed.set_author(name=author, icon_url=avatar)

        embed.add_field(name="Rolls", value=', '.join(formatted), inline=True)
        embed.add_field(name="Result", value=successes, inline=True)
        if specialty is not None:
            embed.add_field(name="Specialty", value=specialty, inline=True)
        if comment is not None:
            embed.add_field(name="Comment", value=comment, inline=False)

        return embed

    #
    # A "traditional" roll, such as 5d10+2.
    #
    def __traditional_roll(self, message, author, avatar):
        m = self.tradx.match(message)
        repeat  = int(m.group('repeat'))
        die     = int(m.group('die'))
        mod     = m.group('mod')
        comment = m.group('comment')

        title = 'Rolling {0}d{1}'.format(repeat, die)

        rolls = self.__roll(repeat, die)
        if mod is not None:
            title += '+' + mod
            rolls.append(int(mod))

        sum = 0
        for roll in rolls:
            sum += roll

        # Create an embed to return
        embed = discord.Embed(title=title, colour=discord.Colour(0x14a1a0))
        embed.set_author(name=author, icon_url=avatar)

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

    # The following rolls all deal with stored rolls and SQLite3 stuff.

    def __query_saved_rolls(self, userid, message):
        # Figure out what kind of query we're doing.

        # Store a new roll or change an old one.
        p = re.compile('^[/!]mw?\s+(?P<name>\w+)\s*=\s*(?P<syn>\d+\s*(?:\d+)?\s*[\w\s]*|\d+d\d+(?:\s*\+\s*\d+))$')
        m = p.match(message)
        if m:
            name   = m.group('name')
            syntax = m.group('syn')
            return self.__store_roll(userid, name, syntax)

        # Use a stored roll.
        p = re.compile('^[/!]m(?P<will>w)?\s+(?P<name>\w+)\s*(?:#\s*(?P<comment>.*))?$')
        m = p.match(message)
        if m:
            name = m.group('name')
            will = m.group('will')
            syntax = self.__retrieve_stored_roll(userid, name)

            if syntax is None:
                return 'Roll doesn\'t exist!'

            comment = m.group('comment')

            roll = '!m ' if will is None else '!mw '
            roll += syntax

            if comment is not None:
                roll += ' # ' + comment
            else:
                roll += ' # ' + name # Provide a default comment

            return roll

        # Delete a stored roll.
        p = re.compile('^[/!]mw?\s+(?P<name>\w+)\s*=\s*$')
        m = p.match(message)
        if m:
            name = m.group('name')
            return self.__delete_stored_roll(userid, name)


        # We have no idea what the user wanted to do.
        return 'Come again?'

    #
    # Store a new roll, or update an old one.
    #
    def __store_roll(self, userid, name, syntax):
        if not self.__is_roll_stored(userid, name):
            # Create the roll
            query = 'INSERT INTO SavedRolls (ID, Name, Syntax) VALUES (\'{0}\', \'{1}\', \'{2}\');'.format(userid, name, syntax)
            self.cursor.execute(query)
            self.conn.commit()

            return 'New roll saved!'
        else:
            # Update an old roll
            query = 'UPDATE SavedRolls SET Syntax=\'' + syntax + '\' WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
            self.cursor.execute(query)
            self.conn.commit()

            return 'Roll updated!'

    #
    # Returns the Syntax for a stored roll.
    #
    def __retrieve_stored_roll(self, userid, name):
        # Find the roll
        query = 'SELECT * FROM SavedRolls WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        result = self.cursor.fetchone()

        if result is None:
            return None

        return result[2]

    #
    # Delete a stored roll.
    #
    def __delete_stored_roll(self, userid, name):
        if not self.__is_roll_stored(userid, name):
            return 'Can\'t delete. Roll not found!'

        query = 'DELETE FROM SavedRolls WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        self.conn.commit()

        return 'Roll deleted!'

    #
    # Returns an embed with all of the user's stored rolls listed.
    #
    def __list_stored_rolls(self, userid):
        query = 'SELECT * FROM SavedRolls WHERE ID=\'' + userid + '\''
        self.cursor.execute(query)
        result = self.cursor.fetchall()

        if len(result) == 0:
            return None

        embed = discord.Embed(colour=discord.Colour(0x1f3446))
        for row in result:
            embed.add_field(name=row[1], value=row[2], inline=False)

        return embed

    #
    # Returns true if a roll by the given name has been stored.
    #
    def __is_roll_stored(self, userid, name):
        return self.__retrieve_stored_roll(userid, name) is not None


# Run it
client = Masquerade()
client.run(os.environ['TZIMISCE_TOKEN'])
