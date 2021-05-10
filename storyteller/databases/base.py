"""Defines the base database class using postgres and autocommit."""
# pylint: disable=no-member

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


    def _execute(self, query, *args, **kwargs):
        """Executes the specified query. Tries to reconnect to the database if there's an error."""
        try:
            self.cursor.execute(query, args)
        except (
            psycopg2.errors.OperationalError, psycopg2.errors.InterfaceError,
            psycopg2.errors.AdminShutdown
        ):
            # Connection got reset for some reason, so fix it
            if "second_attempt" not in kwargs:
                print("Lost database connection. Retrying.")
                self.conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
                self.conn.autocommit = True
                self.cursor = self.conn.cursor()
                self._execute(query, args, second_attempt=True)
            else:
                print("UNRECOVERABLE DATABASE ERROR!")
