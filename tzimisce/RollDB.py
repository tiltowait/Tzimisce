'''Database handler for rolls stored rolls.'''

import os
import re
import psycopg2

class RollDB:
    '''Handles stored rolls, including creation, deletion, listing, and modification.'''

    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS SavedRolls
                              (ID     Text NOT NULL,
                               Name   Text NOT NULL,
                               Syntax Text NOT NULL);''')
        self.conn.commit()


    def query_saved_rolls(self, userid, message):
        '''Parses the message to see what kind of query is needed, then performs it.'''

        # Store a new roll or change an old one.
        pattern = re.compile(r'^[/!]mw?\s+(?P<name>\w+)\s*=\s*(?P<syn>\d+\s*(?:\d+)?\s*[\w\s]*|\d+d\d+(?:\s*\+\s*\d+))$')
        match = pattern.match(message)
        if match:
            name = match.group('name')
            syntax = match.group('syn')
            return self.store_roll(userid, name, syntax)

        # Use a stored roll.
        pattern = re.compile(r'^[/!]m(?P<will>w)?\s+(?P<name>\w+)\s*(?:#\s*(?P<comment>.*))?$')
        match = pattern.match(message)
        if match:
            name = match.group('name')
            will = match.group('will')
            syntax = self.retrieve_stored_roll(userid, name)

            if syntax is None:
                return 'Roll doesn\'t exist!'

            comment = match.group('comment')

            roll = '!m ' if will is None else '!mw '
            roll += syntax

            if comment is not None:
                roll += ' # ' + comment
            else:
                roll += ' # ' + name # Provide a default comment

            return roll

        # Delete a stored roll.
        pattern = re.compile(r'^[/!]mw?\s+(?P<name>\w+)\s*=\s*$')
        match = pattern.match(message)
        if match:
            name = match.group('name')
            return self.delete_stored_roll(userid, name)


        # We have no idea what the user wanted to do.
        return 'Come again?'

    def store_roll(self, userid, name, syntax):
        '''Store a new roll, or update an old one.'''
        if not self.__is_roll_stored(userid, name):
            # Create the roll
            query = 'INSERT INTO SavedRolls (ID, Name, Syntax) VALUES (\'{0}\', \'{1}\', \'{2}\');'.format(userid, name, syntax)
            self.cursor.execute(query)
            self.conn.commit()

            return 'New roll saved!'

        # Update an old roll
        query = 'UPDATE SavedRolls SET Syntax=\'' + syntax + '\' WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        self.conn.commit()

        return 'Roll updated!'

    def retrieve_stored_roll(self, userid, name):
        '''Returns the Syntax for a stored roll.'''
        query = 'SELECT * FROM SavedRolls WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        result = self.cursor.fetchone()

        if result is None:
            return None

        return result[2]

    def delete_stored_roll(self, userid, name):
        '''Delete a stored roll.'''
        if not self.__is_roll_stored(userid, name):
            return 'Can\'t delete. Roll not found!'

        query = 'DELETE FROM SavedRolls WHERE ID=\'' + userid + '\' AND Name=\'' + name + '\';'
        self.cursor.execute(query)
        self.conn.commit()

        return 'Roll deleted!'

    def stored_rolls(self, userid):
        '''Returns an list of all the stored rolls.'''
        query = 'SELECT * FROM SavedRolls WHERE ID=\'' + userid + '\' ORDER BY Name'
        self.cursor.execute(query)
        result = self.cursor.fetchall()

        fields = []
        for row in result:
            fields.append((row[1], row[2]))

        return fields

    def __is_roll_stored(self, userid, name):
        '''Returns true if a roll by the given name has been stored.'''
        return self.retrieve_stored_roll(userid, name) is not None
