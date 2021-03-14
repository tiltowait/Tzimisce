# \[Tzimisce\]
A handy Discord dicebot for classic World of Darkness tabletop RPGs, such as *Vampire: The Masquerade*, *Werewolf: The Apocalyspe*, and *Mage: The Ascension*. At its most basic, it allows for rapid entry of rolls, requiring as few as five keystrokes (including return!) or four taps on a mobile screen. It also possesses some more advanced features, such as roll saving, Willpower-based rolls, and automatic successes.

## Installation
### The Easy Way
Simply [click this link](https://top.gg/bot/642775025770037279) to add the bot to your server. Not ready to add it yet? [Try out the demo server!](https://discord.gg/rK3RFqV)

### The Hard Way
Should you wish to locally run the bot (perhaps to make your own, local changes), you will need to acquire a Discord developer key.

#### Setup
You will need version >=3.9 of [Python](https://www.python.org), as well as [PostgreSQL](https://www.postgresql.org) with SSL support enabled (which may require creating your own certificate key).

Additionally, you will need to use PIP to install `psycopg2` and `discord.py`.

##### Setting the Environment Variables
Store your API token in an environment variable called `TZIMISCE_TOKEN`. Store your PostgreSQL server address in an environment variable named `DATABASE_URL`.

## Usage
For a full command listing, check [the help file](https://tiltowait.github.io/Tzimisce/).

## Requried Permissions
* **Send Messages:** Should be obvious, no?
* **Embed Links:** Used for roll display (outside of compact mode), initiative, help display, etc.
* **Read Message History:** Used for the reply feature
* **Add Reactions:** Used when suggesting macro names and alerting the user that an action declaration was registered

## Troubleshooting
Unable to see the results? Make sure the bot has the permissions above. If you still have problems, you might have website previews disabled. Go into *User Settings -> Text & Images* and enable *Show website preview info from links pasted into chat*. If you *still* have issues, you may have antivirus software that prevents embeds from showing (certain versions of McAfee are known to cause problems).
