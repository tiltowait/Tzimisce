import psycopg2
import os
import re

class RollDB:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS SavedRolls
                              (ID     Text NOT NULL,
                               Name   Text NOT NULL,
                               Syntax Text NOT NULL);''')
        self.conn.commit()


    def query_saved_rolls(self, userid, message):
        # Figure out what kind of query we're doing.

        # Store a new roll or change an old one.
        p = re.compile('^[/!]mw?\s+(?P<name>\w+)\s*=\s*(?P<syn>\d+\s*(?:\d+)?\s*[\w\s]*|\d+d\d+(?:\s*\+\s*\d+))$')
        m = p.match(message)
        if m:
            name   = m.group('name')
            syntax = m.group('syn')
            return self.store_roll(userid, name, syntax)

        # Use a stored roll.
        p = re.compile('^[/!]m(?P<will>w)?\s+(?P<name>\w+)\s*(?:#\s*(?P<comment>.*))?$')
        m = p.match(message)
        if m:
            name = m.group('name')
            will = m.group('will')
            syntax = self.retrieve_stored_roll(userid, name)

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
            return self.delete_stored_roll(userid, name)


        # We have no idea what the user wanted to do.
        return 'Come again?'

    #
    # Store a new roll, or update an old one.
    #
    def store_roll(self, userid, name, syntax):
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
    def retrieve_stored_roll(self, userid, name):
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
    def delete_stored_roll(self, userid, name):
        if not self.__is_roll_stored(userid, name):
            return 'Can\'t delete. Roll not found!'

        query = 'DELETE FROM SavedRolls WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        self.conn.commit()

        return 'Roll deleted!'

    #
    # Returns an list of all the stored rolls.
    #
    def stored_rolls(self, userid):
        query = 'SELECT * FROM SavedRolls WHERE ID=\'' + userid + '\' ORDER BY Name'
        self.cursor.execute(query)
        result = self.cursor.fetchall()

        fields = []
        for row in result:
            fields.append((row[1], row[2]))

        return fields

    #
    # Returns true if a roll by the given name has been stored.
    #
    def __is_roll_stored(self, userid, name):
        return self.retrieve_stored_roll(userid, name) is not None
