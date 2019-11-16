# Tzimisce
A handy Discord dicebot for *Vampire: The Masquerade 20th Anniversary*.

## Installation
The bot is not yet ready for primetime until more testing has been done. Should you wish to locally run the bot, you will need to acquire a Discord developer key, install [PostgreSQL](https://www.postgresql.org), and set up the `SavedRolls` table.

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
*Tzimisce* has a number of options for pool-based rolls and has been designed for quick command entry. As an example, here is how to roll 8 dice, difficulty 4, with a specialty in Koldunism:

```
!m 8 4 Koldunism
```

This compares favorably with Sidekick, where the same command would look like this: `/r 8d10>=4f1t10`. Sidekick’s output also has the potential to be incorrect, as it uses first-edition *Vampire’s* rules instead of *V20’s*.

To see a list of all available options, enter `!m help`.

### Traditional Rolls
*Tzimisce* has limited capability for “traditional” rolls, such as `1d10+5`. It can accept a *single* type of die, plus an *optional, positive* modifier. Example:

```
!m 1d10+5 # Initiative
```

## Improvements Over Sidekick
While the main benefit over Sidekick is brevity, the output is more intelligent when it comes to the *V20* product line. “Negative successes” are only botches when there are zero rolls at or above the difficulty. Botches keep track of “severity” in case of house rules where a “multi-botch” is more detrimental. And Willpower use is clearly stated.

Finally, the output is much more attractive, with color-coding to easily see if a roll was a botch, failure, or success.
