# \[Tzimisce\]
A handy Discord dicebot for classic World of Darkness tabletop RPGs, such as *Vampire: The Masquerade*, *Werewolf: The Apocalyspe*, and *Mage: The Ascension*. At its most basic, it allows for rapid entry of rolls, requiring as few as five keystrokes (including return!). It also possesses some more advanced features, such as macros, Willpower use, automatic successes, and statistical analysis.

## Installation
### The Easy Way
Simply [click this link](https://top.gg/bot/642775025770037279) to add the bot to your server. Not ready to add it yet? [Try out the demo server!](https://discord.gg/rK3RFqV)

### The Hard Way
Should you wish to run the bot locally, you will need to obtain a Discord developer key [here](https://discord.com/developers/applications).

#### Setup
\[Tzimisce\] requires version >=3.9 of [Python](https://www.python.org) and [PostgreSQL](https://www.postgresql.org) with SSL support enabled (which means you need an SSL certificate).

Additionally, you will need to use PIP to install [psycopg2](https://pypi.org/project/psycopg2/), [discord.py](https://pypi.org/project/discord.py/), and [dice](https://pypi.org/project/dice/). You can quickly install these dependencies with `pip -r requirements.txt`.

##### Setting the Environment Variables
Store your API token in an environment variable called `TZIMISCE_TOKEN`. Store your PostgreSQL server address in an environment variable named `DATABASE_URL`.

#### Run the Bot
Make sure Postgres is running, then enter `python3 masquerade.py` to run the bot.

## Usage
For a full command listing, check [the help file](https://tiltowait.github.io/Tzimisce/).

## Requried Permissions
* **Send Messages:** Should be obvious, no?
* **Embed Links:** Used for roll display (outside of compact mode), initiative, help display, etc.
* **Read Message History:** Used for the reply feature
* **Add Reactions:** Used when suggesting macro names and alerting the user that an action declaration was registered
* **Use External Emoji:** For displaying individual dice throws

## Troubleshooting
Unable to see the results? Make sure the bot has the permissions above. If you still have problems, you might have website previews disabled. Go into *User Settings -> Text & Images* and enable *Show website preview info from links pasted into chat*. If you *still* have issues, you may have antivirus software that prevents embeds from showing (certain versions of McAfee are known to cause problems).
