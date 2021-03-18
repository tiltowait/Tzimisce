**\[Tzimisce\]** is a Discord dicebot for White Wolf's World of Darkness RPGs, including **Vampire: The Masquerade**, **Mage: The Ascension**, **Werewolf: The Apocalypse**, and **Wraith: The Oblivion**. It features simple syntax; easy-to-read, color-coded output; and a number of advanced features.

> ### Quick Links
> * **[Invite \[Tzimisce\] to your server](https://top.gg/bot/642775025770037279)**
> * **[Join the support server](https://discord.gg/rK3RFqV)**
> * **[View the source code](https://github.com/tiltowait/Tzimisce)**
> * **[Become a patron](https://www.patreon.com/tzimisce)**

---

# Commands

## Storyteller Rolls

<!-- tabs:start -->

#### ** Basics **

```
!m <pool> [difficulty] [specialty] # comment
```

* `pool` — Number of dice to roll
* `difficulty` — Default 6. Must be between 2-10
* `specialty` — By default, causes 10s to count as double successes
* `# comment` — Label to be applied to the roll. The `#` is required!

?> `difficulty`, `specialty`, and `# comment` are all optional.

#### Examples

* `!m 5` — Roll 5 dice at difficulty 6
* `!m 5 7 # Mask of 1000 Faces` — 5 dice, difficulty 7, with a comment
* `!m 8 5 Domineering # Command` — 8 dice, difficulty 5, specialty "Domineering", and a comment

#### ** Willpower **

```
!mw <syntax>
```

Adding Willpower to a roll adds an extra success which cannot be canceled by botches. The rest of the roll syntax is the same. May be combined with other options.

#### ** Auto-Successes **

```
!m <pool> <difficulty> <autos> [specialty] # comment
```

In order to add Potence-style automatic successes, both the `pool` and the `difficulty` must be supplied. May be combined with other options.

?> Unlike Willpower, these auto-successes may be canceled by ones.

#### ** Options **

|                 |       |                                                   |
|-----------------|-------|---------------------------------------------------|
| Upgrade botches | `!mz` | Promotes botches to regular failures              |
| Compact mode    | `!mc` | Outputs results in plain text instead of an embed |

?> These options, as well as Willpower, may be combined. Thus, `!mwcz` becomes a compact Willpower roll that cannot botch (though by definition, a Willpower roll can't botch).

<!-- tabs:end -->

## Traditional Rolls

```
!m XdY+...+n # comment
```

\[Tzimisce\] can perform traditional rolls, such as 1d10+5, 2d10+3d6, etc. Currently, only addition is allowed. This may be combined with **compact mode** (`!mc`). Other options are ignored.

## Macros

\[Tzimisce\] features macro-support, including one-off modifications. Macros support both pool-based and traditional dice rolls.

<!-- tabs:start -->

#### ** Create **

```
!m <macro-name> = <syntax> # comment
```

The `macro-name` must not contain spaces but can contain both `-` and `_` characters. The roll syntax can be any valid roll. If supplied, the `# comment` will be used every time you use the macro unless overridden.

If the macro already exists, invoking this command will overwrite it. In this case, the previously stored comment will be retained unless a new one is supplied.

To use a macro, simply type `!m <macro-name>`. Macros support all the standard roll options (compact mode, Willpower, botch upgrades).

!> **Note:** Saving a macro does not roll the macro!

#### Examples

* `!m attack = 7 Graceful # Dex + Brawl` — Saves both the roll syntax and the comment
* `!m attack` — Rolls the `attack` macro
* `!m attack # Using claws` — Rolls the `attack` macro, supplying a different comment

#### ** Modify **

#### Permanent

Updating a macro is as simple as using the creation command again. Note that if the current macro has a comment and you do not supply a new one, the old comment will be retained.

You may update *just the comment* with `!m <macro_name> c= <new_comment>`.

#### One-Time

It is also possible to modify a macro for a single roll (for instance, if your character suffers from wound penalties). The syntax for this is:

```
!m <macro-name> <pool-mod> [diff-mod] # comment
```

* `pool-mod` — A positive or negative integer that adds or subtracts from the dice pool
* `diff-mod` — *(Optional)* A positive or negative integer that adds or subtracts from the difficulty. If no sign is given, then the difficulty will be *set* to `diff-mod`

#### Examples

* `!m attack +2` — Rolls the `attack` macro with two extra dice
* `!m attack 0 +1` — Rolls the `attack` macro with zero extra dice, at one higher difficulty than normal
* `!m attack -1 5` — Rolls the `attack` macro with one fewer die, at difficulty 5

!> `pool-mod` requires a +/- sign!

!> If the modification reduces the pool to 0 or brings the difficulty outside of the range of 2-10, then the command will fail.

#### ** Delete **

| Command                                   | Syntax              |
|-------------------------------------------|---------------------|
| **Delete `macro-name`**                   | `!m <macro-name> =` |
| **Delete all your macros on this server** | `!m $delete-all`    |

!> These actions cannot be undone!

#### ** List **

|                  |                                         |
|------------------|-----------------------------------------|
| `!m $`           | DMs a list of your macros on the server |


<!-- tabs:end -->

## Initiative

<!-- tabs:start -->

#### ** Roll **
```
!mi <mod> [character]
```

* `mod` — The Dex + Wits modifier
* `character` — The character name

?> If `character` is not supplied, it will default to your display name. By supplying `character`, you may roll for an arbitrary number of characters, NPCs, etc.

#### ** Declare **
```
!mi dec <action> [-n character]
```

* `action` — The action to be declared

If the `-n character` option is set, the action will be declared under the name of `character`. For instance: `!mi dec Ends the world -n Caine` will declare that Caine intends to end the world.

!> If `character` is not already in the initiative table, the command will fail.

#### ** Other **

| Command                    | Syntax                                   |
|----------------------------|------------------------------------------|
| **Remove a character**     | `!mi remove [character]`                 |
| **Reroll all initiative**  | `!mi reroll`  (removes declared actions) |
| **Clear initiative table** | `!mi clear`                              |

<!-- tabs:end -->

# Customization
**\[Tzimisce\]** has a number of settings that can be changed on a per-server basis.

<!-- tabs:start -->

#### ** Parameters **

| Parameter       | Description                                                                           |
|-----------------|---------------------------------------------------------------------------------------|
| `use_compact`   | Always use compact mode for rolls                                                     |
| `xpl_always`    | On pool-based rolls, tens explode (roll an additional die, recursively)               |
| `xpl_spec`      | When rolling a specialty, tens explode                                                |
| `no_double`     | Tens *never* count as double successes                                                |
| `always_double` | Tens *always* count as double successes                                               |
| `nullify_ones`  | When using the `z` (upgrade botches) roll option, ones do not subtract from successes |
| `default_diff`  | The default difficulty for pool-based rolls. Default `6`.                             |
| `prefix`        | Change the bot's invocation prefix. Defaults to `!` and `/`                           |

?> Unless specified otherwise, these parameters default to `false`.

#### ** Commands **

| Command                        | Syntax                       |
|--------------------------------|------------------------------|
| **View server settings**       | `!m set`                     |
| **View parameter description** | `!m set <parameter>`         |
| **Set parameter**              | `!m set <parameter> <value>` |

!> Setting the `prefix` ***does not*** change the command names. For instance, entering `/m set prefix ?` will make the standard roll command `?m`, initiative actions `?mi`, etc.

<!-- tabs:end -->

# Troubleshooting
If you cannot see rolls, check that the bot has the permissions below. If it still doesn't work ensure you have the Discord setting, "Show website preview info from links pasted into chat", enabled under Text & Images. If you *still* cannot see rolls, you may have antivirus that's blocking them (McAfee and possibly some others do this).

## Required Permissions <!-- {docsify-ignore} -->

* **Send Messages:** Should be obvious, no?
* **Embed Links:** Used for roll display (outside of compact mode), initiative, help display, etc.
* **Read Message History:** Used for the reply feature

## Optional Permissions <!-- {docsify-ignore} -->

* **Add Reactions:** Used when suggesting macro names and alerting the user that an action declaration was registered. If not granted, the user can't click to automatically roll a macro suggestion, and there will be no feedback that an action declaration has been logged
* **Use external emojis:** Used for color-coded display of pool-based dice results. If not granted, it will default to plaintext
