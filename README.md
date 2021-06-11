<p align="center">
  <img src="images/tzimisce-logo.webp" alt="Tzimisce Dicebot" style="width: auto, max-height: 125px" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9-blue" alt="Requires Python 3.9" />
  <img src="https://img.shields.io/badge/discord.py-1.7.2-brightgreen" alt="Requires discord.py 1.7.2" />
  <img src="https://img.shields.io/badge/psycopg2-2.8.6-yellow" alt="Requires psycopg2 2.8.6" />
  <img src="https://img.shields.io/badge/dice-3.1.2-green" alt="Requires dice 3.1.2" />
</p>

<p align="center">
  <a href="https://top.gg/bot/642775025770037279">
    <img src="https://top.gg/api/widget/642775025770037279.svg" alt="[Tzimisce] on the Discord Bot List" />
  </a>
</p>

**[Tzimisce]** is a  Discord dicebot for classic World of Darkness tabletop RPGs, including *Vampire: The Masquerade*, *Werewolf: The Apocalyspe*, *Mage: The Ascension*, and others. Combined with its user-friendly output, [Tzimisce] is far easier to use than common "universal" dice rollers. In addition, the bot possesses advanced features such as macros, Willpower use, automatic successes, initiative management, and statistical analysis.

## Getting Started
### Adding [Tzimisce] to Your Server
Simply [click this link](https://top.gg/bot/642775025770037279) to add the bot to your server. Feel free to vote and leave a review while you're at it; it's greatly appreciated. Not ready to add it yet? [Try out the demo server!](https://discord.gg/rK3RFqV)

### Usage
Base syntax is simple: `/m pool difficulty specialty`. The specialty is optional. If `difficulty` isn't supplied, it defaults to 6. If you want to add a comment, simply append a `#` and start typing.

**Example:** 7 dice at difficulty 5 with a specialty in climbing and a comment of "dex + athletics":

```
/m 7 5 Climbing # Dex + Athletics
```

But that's not all [Tzimisce] can do! It also features macro support, initiative, server-wide customization, and more. For a full command listing, check [the help page](https://storyteller-bot.com).

### Requried Permissions
* **Send Messages:** Should be obvious, no?
* **Embed Links:** Used for roll display (outside of compact mode), initiative, help display, etc.
* **Read Message History:** Used for the reply feature
* **Add Reactions:** Used when suggesting macro names and alerting the user that an action declaration was registered
* **Use External Emoji:** For displaying individual dice throws

## Troubleshooting
Unable to see the results? Make sure the bot has the permissions above. If you still have problems, you might have website previews disabled. Go into *User Settings -> Text & Images* and enable *Show website preview info from links pasted into chat*. If you *still* have issues, you may have antivirus software that prevents embeds from showing (certain versions of McAfee are known to cause problems).

## Advanced Installation
Should you wish to run the bot locally, you will need to obtain a Discord developer key [here](https://discord.com/developers/applications).

### Setup
\[Tzimisce\] requires version >=3.9 of [Python](https://www.python.org) and [PostgreSQL](https://www.postgresql.org) with SSL support enabled (which means you need an SSL certificate). You will also need a Discord developer token and, if you intend on making your fork available on [the Discord Bot List](https://top.gg), a top.gg API token.

Finally, you will need to use PIP to install [psycopg2](https://pypi.org/project/psycopg2/), [discord.py](https://pypi.org/project/discord.py/), [dice](https://pypi.org/project/dice/), and [topggpy](https://pypi.org/project/topggpy/). Typically, you can install these dependencies with `pip -r requirements.txt`, but the command may differ on your system if you have multiple Python versions installed.

#### Setting the Environment Variables
Store your API token in an environment variable called `TZIMISCE_TOKEN`. Store your PostgreSQL server address in an environment variable named `DATABASE_URL`. (Optional: If listing in the Discord Bot List, set `TOPGG_TOKEN`.)

### Run the Bot
Make sure Postgres is running, then enter `python masquerade.py` to run the bot. Like before, this command may differ if your system has multiple Python versions installed.
