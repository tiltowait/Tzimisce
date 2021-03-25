"""Package parse. Contains the various argument parsers."""

from .pool import pool, is_valid_pool
from .traditional import traditional, is_valid_traditional
from .db import database
from .initiative import initiative, initiative_removal, initiative_declare
from .response import Response

def is_valid_roll(syntax: str) -> bool:
    """Determines whether the syntax is a valid traditional/pool roll."""
    return is_valid_pool(syntax) or is_valid_traditional(syntax)
