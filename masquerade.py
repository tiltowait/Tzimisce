import tzimisce
import os

client = tzimisce.Masquerade()
client.run(os.environ['TZIMISCE_TOKEN'])
