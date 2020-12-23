# \[Tzimisce\]
A handy Discord dicebot for *Vampire: The Masquerade 20th Anniversary* and other "20th Anniversary" White Wolf Storyteller games. At its most basic, it allows for rapid entry of rolls, requiring as few as five keystrokes (including return!) or four taps on a mobile screen. It also possesses some more advanced features, such as roll saving, Willpower-based rolls, and automatic successes.

## Installation
### The Easy Way
Simply [click this link](https://discordapp.com/api/oauth2/authorize?client_id=642775025770037279&permissions=0&scope=bot) to add the bot to your server. Not ready to add it yet? [Try out the demo server!](https://discord.gg/rK3RFqV)

### The Hard Way
Should you wish to locally run the bot (perhaps to make your own, local changes), you will need to acquire a Discord developer key.

#### Setup
You will need version 3.7 or greater of [Python](https://www.python.org), as well as [PostgreSQL](https://www.postgresql.org) with SSL support enabled (which may require creating your own certificate key).

Additionally, you will need to use PIP to install `psycopg2` and `discord.py`.

##### Setting the Environment Variables
Store your API token in an environment variable called `TZIMISCE_TOKEN`. Store your PostgreSQL server address in an environment variable named `DATABASE_URL`.

## Usage
For a full command listing, check [the help file](https://tiltowait.github.io/Tzimisce/).

## Troubleshooting
Unable to see the results? You probably have website previews disabled. Go into *User Settings -> Text & Images* and enable *Show website preview info from links pasted into chat*.
