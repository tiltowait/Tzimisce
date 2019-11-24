# Tzimisce
A handy Discord dicebot for *Vampire: The Masquerade 20th Anniversary*.

## Installation
### The Easy Way
Simply [click this link](https://discordapp.com/api/oauth2/authorize?client_id=642775025770037279&permissions=67584&scope=bot) to add the bot to your server.

### The Hard Way
Should you wish to locally run the bot (perhaps to make your own, local changes), you will need to acquire a Discord developer key.

#### Setup
You will need version 3.7 or greater of [Python](https://www.python.org), as well as [PostgreSQL](https://www.postgresql.org) with SSL support enabled (which may require creating your own certificate key).

Additionally, you will need to install `psycopg2` and `discord.py`.

### Setting the Environment Variables
Store your API token in an environment variable called `TZIMISCE_TOKEN`. Store your PostgreSQL server address in an environment variable named `DATABASE_URL`.

## Usage
### Pool-Based Rolls
*Tzimisce* has a number of options for pool-based rolls and has been designed for quick command entry. As an example, here is how to roll 8 dice, difficulty 4, with a specialty in Koldunism:

```
!m 8 4 Koldunism
```

This compares favorably with Sidekick, where the same command looks like this: `/r 8d10>=4f1t10`. Sidekick’s output is also often incorrect, as it uses first-edition *Vampire’s* rules instead of *V20’s*.

To see a list of all available options, enter `!m help`.

### Traditional Rolls
*Tzimisce* has moderately robust capability for “traditional” rolls, such as `1d10+5`. Invocation is simple:

```
!m 1d10+5 # Initiative
```

You may enter an arbitrary number of dice and modifiers, *so long as they are all additive*.

```
!m 1d10+2d6+3
```

As of now, *Tzimisce* does not know how to subtract, multiply, divide, etc. on traditional rolls.

## Improvements Over Sidekick
While the main benefit over Sidekick is command brevity, the output is more intelligent when it comes to the *V20* product line. “Negative successes” are only botches when there are zero rolls at or above the difficulty. Botches keep track of “severity” in case of house rules where a “multi-botch” is more detrimental. And Willpower use is clearly stated.

Finally, the output is much more attractive, with color-coding to easily see if a roll was a botch, failure, or success.
