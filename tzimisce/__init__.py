"""Package tzimisce. The user need only know about Masquerade, the client class."""

from tzimisce import masquerade
from tzimisce import initiative
from tzimisce import roll

# This is a defaultdict, lambda None
CUSTOM_PREFIXES = masquerade.database.get_all_prefixes()

def get_prefix(guild) -> tuple:
    """Returns the guild's prefix. If the guild is None, returns a default."""
    default_prefixes = ("/", "!")

    if guild:
        prefix = CUSTOM_PREFIXES[guild.id]
        if prefix:
            return (prefix,)
        return default_prefixes

    return default_prefixes
