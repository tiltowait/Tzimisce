"""Package storyteller. The user need only know about Masquerade, the client class."""

from storyteller import engine
from storyteller import initiative
from storyteller import roll
from storyteller.databases import SettingsDB

# This is a defaultdict, lambda None
INITIATIVE_MANAGERS = engine.database.get_initiative_tables()

settings = SettingsDB()
