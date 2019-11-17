"""Creates and connects an instance of the Tzimisce dicebot."""

import os
import tzimisce

CLIENT = tzimisce.Masquerade()
CLIENT.run(os.environ["TZIMISCE_TOKEN"])
