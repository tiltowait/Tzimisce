"""base.py - Defines the base database class using postgres and autocommit."""
# pylint: disable=no-member

import os
import psycopg2


class Database:
    """Base database class. This should never be instantiated directly."""
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()


    def _execute(self, query: str, *args):
        """
        Execute the specified query. Tries to reconnect to the database if there's an error.
        Args:
            query (str): The SQL query to enact
            *args: The values associated with the query
            **kwargs: Used for determining if this is a second execution attempt
        """
        try:
            # Check first if the database connection is still valid
            self.cursor.execute("SELECT 1")
        except psycopg2.Error:
            # Though we are going to attempt to reconnect to the database,
            # technically this will catch other errors as well, such as bad
            # SQL syntax. We will trust that our syntax is correct, given it is
            # programmatically generated.
            self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
        finally:
            self.cursor.execute(query, args)
