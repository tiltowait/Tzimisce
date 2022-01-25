"""debug.py - Debugging constants and facilities."""

import os

from dotenv import load_dotenv

load_dotenv()

GUILDS = [758492110591885373] if "DEBUG" in os.environ else None
