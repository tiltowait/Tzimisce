# Masquerade-Bot
A handy Discord bot for handling rolls in a *Vampire: The Masquerade 20th Anniversary* game.

## Installation
As of now, the bot requires the user to self-host the bot, including creating an API token through Discord. Store the token in `token.txt` in the same directory as `masquerade.py`.

## Usage
### Standard
*Masquerade-Bot* is designed for ease of use, particularly on mobile. On an iPhone, entering a roll takes as few as 10 taps on the keyboard, a dramatic improvement over Sidekick’s 21.
```
!m <pool> <difficulty>
```

### Optional Arguments
There are two optional arguments: `[specialty]` and `# comment`:
```
!m 8 6 Koldunism # Int + Occult
```
This example rolls a pool of 8 dice, difficulty 6, with a specialty of *Koldunism*, and a comment *Int + Occult*. When tagging a specialty, tens count as double.

### Willpower
Rolls using temporary Willpower may be performed using the `!mw` command, which is otherwise identical to the standard invocation. Such rolls have a guaranteed success and will never botch.

## Improvements Over Sidekick
While the main benefit over Sidekick is brevity, the output is more intelligent when it comes to the *V20* product line. “Negative successes” are only botches when there are zero rolls at or above the difficulty. Botches keep track of “severity” in case of house rules where a “multi-botch” is more detrimental. And Willpower use is clearly stated.

## Limitations
* It is also unable to save rolls. There are no plans to support this feature at this time.

## Planned Improvements
* Code refactoring and documentation
* Proper hosting
