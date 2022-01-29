"""databases module - defines various databases used by the bot."""

from .database import RollDB
from .settings import SettingsDB
from .initiative import InitiativeDB
from .metamacros import MetaMacroDB
from .statistics import StatisticsDB

# Kludgy way of initiating the databases if they don't exist
_ = SettingsDB()
_ = RollDB()
