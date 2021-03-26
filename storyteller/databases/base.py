"""Defines the base database class using postgres and autocommit."""

import os
import psycopg2

class Database:
    """Base database class."""
    # pylint: disable=too-few-public-methods

    def __init__(self):
        # Set up the database
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def _execute(self, query, *args):
        """Executes the specified query. Tries to reconnect to the database if there's an error."""
        try:
            self.cursor.execute(query, args)
        except psycopg2.errors.AdminShutdown: # pylint: disable=no-member
            # Connection got reset for some reason, so fix it
            print("Lost database connection. Retrying.")
            self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, args) # Reconnected, so try again!
