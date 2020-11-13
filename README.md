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
### Pool-Based Rolls
*\[Tzimisce\]'s* basic (and most common) command is:
```
/m <pool> [difficulty] [autos] [specialty] [# comment]
```

* `pool`: The number of d10s to roll.
* `difficulty` (optional): The target number for each die in the pool. Defaults to 6. If the supplied difficulty is below 2 or above 10, the bot will automatically change the difficulty to the nearest threshold.
* `specialty` (optional): If supplied, a result of ten on an individual die will be doubled.
* `# comment` (optional): A comment to attach to the roll. The `#` is required!
* `autos` (optional): The number of automatic successes to apply. These are cancelable by botches. If using `autos`, `difficulty` ***must*** be supplied!

#### Examples
Roll 5 dice, difficulty 6:
```
/m 5
```

Roll 8 dice, difficulty 7, with a specialty in persuasion, and a comment:
```
/m 8 7 Persuasion # Charisma + Leadership
```

Roll 5 dice, difficulty 6, with two auto-successes:
```
/m 5 6 2
```

#### Willpower
Willpower may be added to any roll by adding the `w` flag:
```
/mw 5
```

The preceding rolls five dice and adds a success *that cannot be removed by botches*.

#### And more!
See the bot's in-app help comand by entering `/m help`.

### Traditional Rolls
*\[Tzimisce\]* has moderately robust capability for “traditional” rolls, such as `1d10+5`. Invocation is simple:

```
/m 1d10+5 # Initiative
```

You may enter an arbitrary number of dice and modifiers, *so long as they are all additive*.

```
/m 1d10+2d6+3
```

At this moment, *\[Tzimisce\]* does not know how to subtract, multiply, divide, etc. on traditional rolls.

## Troubleshooting
Unable to see the results? You probably have website previews disabled. Go into *User Settings -> Text & Images* and enable *Show website preview info from links pasted into chat*.
