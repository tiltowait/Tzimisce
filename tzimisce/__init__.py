"""Package tzimisce. The user need only know about Masquerade, the client class."""

from tzimisce import masquerade
from tzimisce import initiative
from tzimisce import roll
from tzimisce.settings import SettingsDB

# This is a defaultdict, lambda None
INITIATIVE_MANAGERS = masquerade.database.get_initiative_tables()

settings = SettingsDB()
