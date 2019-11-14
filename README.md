# Tzimisce
A handy Discord dicebot for *Vampire: The Masquerade 20th Anniversary*.

## Installation
The bot is not yet ready for primetime until more testing has been done. Should you wish to locally run the bot, you will need to set up a Discord developer key, install [PostgreSQL](https://www.postgresql.org), and set up the `SavedRolls` table.

Additionally, it requires `psycopg2` and `discord.py`.

### Creating the Tables
```
CREATE TABLE SavedRolls
(ID    Text NOT NULL,
Name   Text NOT NULL,
Syntax Text NOT NULL);
```

### Setting the token
Store your API token in an environment variable called `TZIMISCE_TOKEN`.

## Usage
### Pool-Based Rolls
*Tzimisce* is designed for ease of use, particularly on mobile. On an iPhone, entering a roll takes as few as 7 taps on the on-screen keyboard, a dramatic improvement over Sidekick’s 21.
```
!m <pool> [difficulty]
```

#### Optional Arguments
There are three optional arguments: `[difficulty]`, `[specialty]`, and `# comment`:
```
!m 8 5 Koldunism # Int + Occult
```
This example rolls a pool of 8 dice, difficulty 5, with a specialty of *Koldunism*, and a comment *Int + Occult*. When tagging a specialty, tens count as double.

If `difficulty` isn’t supplied, it defaults to 6.

#### Willpower
Rolls using temporary Willpower may be performed using the `!mw` command, which is otherwise identical to the standard invocation. Such rolls have a guaranteed success and will never botch.

### Traditional Rolls
*Tzimisce* has limited capability for “traditional” rolls, such as `1d10+5`. It can accept a *single* type of die, plus an *optional, positive* modifier. A more robust system is planned.

## Improvements Over Sidekick
While the main benefit over Sidekick is brevity, the output is more intelligent when it comes to the *V20* product line. “Negative successes” are only botches when there are zero rolls at or above the difficulty. Botches keep track of “severity” in case of house rules where a “multi-botch” is more detrimental. And Willpower use is clearly stated.

Finally, the output is much more attractive, with color-coding to easily see if a roll was a botch, failure, or success.
