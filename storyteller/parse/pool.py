"""pool.py - Performs pool-based rolls for the user."""

import re
from typing import Union

import discord
from storyteller import roll, engine # pylint: disable=cyclic-import
from .response import Response


__poolx = re.compile(
    r"^(?P<pool>-?\d+)[\s@]?(?P<difficulty>\d+)?\s?(?P<auto>[+-]?\d+)?(?: (?P<specialty>\D[^#]*))?$"
)

# These embed colors are used for giving at-a-glance notice if a roll was
# successful or not, with gradually brightening greens denoting higher degrees
# of success (and gray and red denoting failure and botch, respectively)
EXCEPTIONAL_COLOR = 0x00FF00
SUCCESS_COLOR = 0x0DC06B
MARGINAL_COLOR = 0x14A1A0
FAIL_COLOR = 0X777777
BOTCH_COLOR = 0XfF0000


async def pool(ctx, command: dict) -> Response:
    """
    Parse user input to determine if they are performing a standard "pool" roll.
    If they are, roll it and return the results.
    Args:
        ctx (discord.ext.commands.Context): The bot invocation context
        command (dict): The user's syntax, comment, invocation parameters, and
                        server settings
    """
    pool_command = __poolx.match(command["syntax"])
    if pool_command:
        # pool_command's capture groups contain a great deal of information
        # about the user's intentions, including pool, difficulty, and specialty
        command.update(pool_command.groupdict())
        result = __pool_roll(ctx, command)

        # Wrap up the roll result in a Response type
        if isinstance(result, discord.Embed):
            return Response(Response.POOL, embed=result)

        return Response(Response.POOL, content=result)



def is_valid_pool(syntax: str) -> bool:
    """
    Determine whether the syntax is a valid pool roll.
    Args:
        syntax (str): The user's command syntax
    Returns (bool): True if the syntax is vaild for a pool roll
    """
    return __poolx.match(syntax) is not None


def __pool_roll(ctx, command: dict) -> Union[str, discord.Embed]:
    """
    Perform a pool-based roll.
    Args:
        ctx (discord.ext.commands.Context): The bot invocation context
        command (dict): The user's syntax, comment, invocation parameters, and
                        server settings
    Returns (Union[str, discord.Embed]): The formatted roll result
    """
    will = command["will"]
    compact = command["use_compact"]
    dice_pool = int(command["pool"])

    if not 1 <= dice_pool <= 100:
        return f"Sorry, pools must be between 1 and 100. *(Input: {dice_pool})*"

    # Set up the base roll options
    options = {
        "never_botch": command["never_botch"],
        "ignore_ones": command["ignore_ones"],
        "wp_cancelable": command["wp_cancelable"],
        "unsort_rolls": command["unsort_rolls"]
    }

    # If the user did not supply a difficulty, use the server default
    difficulty = int(command["difficulty"] or command["default_diff"])

    # Chronicles of Darkness uses different rules than WoD, particularly where
    # difficulty is concerned, so we need a special case just for that
    chronicles = command["chronicles"]
    if chronicles:
        difficulty = command["default_diff"]

        # The second argument in a CofD roll is explosion target
        if command["difficulty"] is not None:
            options["xpl_target"] = int(command["difficulty"])
        else:
            options["xpl_target"] = 10

    if not chronicles and not 2 <= difficulty <= 10:
        return f"Whoops! Difficulty must be between 2 and 10. *(Input: {difficulty})*"

    # By RAW, the difficulty of a CofD roll is always 8; however, the bot allows
    # server admins to change the default difficulty if they wish. Therefore, we
    # have to make sure the user isn't somehow trying to have unsuccessful dice
    # explode, which would just be weird.
    if chronicles and not difficulty <= options["xpl_target"] <= 10:
        return f"Whoops! X-Again must be between {difficulty} and 10, not {options['xpl_target']}."

    # Sometimes, a roll may have auto-successes that can be canceled by 1s.
    autos = int(command["auto"] or 0)

    specialty = command["specialty"] # Doubles 10s if set
    options["double_tens"] = __should_double(command, specialty is not None)

    if not chronicles: # Regular CofD rolls *always* explode
        options["xpl_target"] = __explosion_target(command, specialty is not None)

    # Finally, roll it!
    results = roll.Pool(dice_pool, difficulty, autos, will, chronicles, options)

    # OUTPUT GENERATION

    comment = command["comment"]

    if compact:
        # The user or the server has requested compact formatting instead of Discord
        # embeds. This format has the side effect of being nicer for screen readers
        return __build_compact(results, specialty, comment)

    # EMBED CREATION

    title = f"Pool {dice_pool}, diff. {difficulty}"
    if command["chronicles"]:
        title = f"Pool {dice_pool}, {options['xpl_target']}-again"

    if autos != 0:
        title += f", {__pluralize_auto_successes(autos)}"

    # Let the user know if we aren't allowing botches
    if command["never_botch"] and not command["chronicles"]:
        title += ", no botch"

    # Inform the user of any explosions
    if results.explosions > 0:
        explosions = "explosion" if results.explosions == 1 else "explosions"
        title += f" (+{results.explosions} {explosions})"

    return __build_embed(ctx, command["override"], results, specialty, will, autos, title, comment)


def __build_embed(
    ctx: discord.ext.commands.Context,
    override: bool,
    results: roll.Pool,
    specialty: str,
    will: bool,
    autos: int,
    title: str,
    comment: str
):
    """
    Build an embed for displaying the roll results.
    Args:
        ctx (discord.ext.commands.Context): The bot invocation context
        override (bool): Whether the user overrode a macro's parameters
        results (roll.Pool): The results of a pool-type roll
        specialty (Optional[Str]): The specialty the user invoked
        will (bool): Whether Willpower was used on the roll
        autos (int): The number of automatic successes for the roll
        title (str): The title for the embed
        comment (str): The description text for the roll
    Returns (discord.Embed): The formatted embed
    """
    # pylint: disable=too-many-arguments

    # The embed's color indicates if the roll succeeded, failed, or botched
    color = FAIL_COLOR
    if results.successes >= 5:
        color = EXCEPTIONAL_COLOR
    elif results.successes >= 3:
        color = SUCCESS_COLOR
    elif results.successes > 0:
        color = MARGINAL_COLOR
    elif results.successes < 0:
        color = BOTCH_COLOR

    # Set up the embed fields
    fields = []
    if override:
        fields.append(("Macro override", override, False))

    # Display individual dice as emoji, if available
    can_use_emoji = ctx.channel.permissions_for(ctx.me).external_emojis

    if can_use_emoji and len(results.dice) <= 40:
        names = results.dice_emoji_names
        emojis = __emojify_dice(ctx, names, will, autos)
        fields.append(("Dice", emojis, True))
    else:
        fields.append(("Dice", results.formatted_dice, True))

    if specialty:
        fields.append(("Specialty", specialty, True))

    return engine.build_embed(
        author=ctx.author, title=results.formatted_result, header=title, color=color, fields=fields,
        footer=comment
    )


def __build_compact(results: str, specialty: str, comment: str) -> str:
    """
    Generate a compact result string for the roll.
    Args:
        results (roll.Pool): The roll results
        specialty (str): The specialty the user invoked for the roll
        comment (str): The description text for the roll
    Returns (str): The formatted compact result string
    """
    compact_string = ""

    if comment:
        compact_string += f"> {comment}\n\n"

    compact_string += f"{results.formatted_dice}"
    if specialty:
        compact_string += f"   ({specialty})"

    compact_string += f"\n**{results.formatted_result}**"

    return compact_string

def __pluralize_auto_successes(autos: int) -> str:
    """
    Generate a pluralized string of the form "+/-X success(es)"
    Args:
        autos (int): The number of automatic successes
    Returns (str): The formatted string
    """
    string = f"{autos:+} success"
    if abs(autos) > 1:
        string += "es"

    return string


# Emoji stuff

# Dice are programmatically converted to their emoji name. The name is composed of
# two or three elements: specialty/success/failure/botch + the number. A successful 6
# becomes 's6', whereas a failing 2 becomes 'f2'. 'ss10' means a specialty 10, and
# 'b1' means a botching 1. The numbers correspond to the Discord ID of the emoji
# as stored in the Tzimisce Dicebot Support server.

emojidict = {
    "ss10": 821609995811553280,
    "s10": 821613862737674261,
    "s9": 821613862805700618,
    "s8": 821613862457180212,
    "s7": 821613862490341408,
    "s6": 821613862830080031,
    "s5": 821613862524420157,
    "s4": 821613862783549480,
    "s3": 821613862797049876,
    "s2": 821613862554042389,
    "f9": 821601300541734973,
    "f8": 821601300541210674,
    "f7": 821601300541603870,
    "f6": 821601300210253825,
    "f5": 821601300495335504,
    "f4": 821601300486553600,
    "f3": 821601300281425962,
    "f2": 821601300483014666,
    "f1": 821601300420493362,
    "b1": 821601300310392832
}


def __emojify_dice(ctx, emoji_names: list[str], willpower: bool, autos: int) -> str:
    """
    Convert a roll string to an emoji string.
    Args:
        ctx (discord.ext.commands.Embed): The bot invocation context. Used for retrieving emoji
        names (list[str]): The names of the emoji to use
        willpower (bool): Whether Willpower was used in the roll
        autos (int): The number of auto-successes in the roll
    """

    # This is way more complex than it needs to be, but I don't feel like fixing it
    emojis = []
    for emoji_name in emoji_names:
        emoji = emojidict[emoji_name]
        if isinstance(emoji, int):
            emoji = ctx.bot.get_emoji(emoji)

            # Cache the emoji for faster lookup, but only if we successfully
            # fetched one
            if emoji:
                emoji = str(emoji)
                emojidict[emoji_name] = emoji
            else:
                # For some reason, we failed to capture an emoji. This typically
                # means a Discord error of some sort and is usually recoverable
                # in the long term. For now, we need to extract the number from
                # the string and present that to the user.
                emoji = re.search(r"\d+", emoji_name).group(0) # Guaranteed to have a match

        emojis.append(emoji + "​")

    emoji_string = " ".join(emojis)

    if willpower:
        emoji_string += " *+WP*"
    if autos != 0:
        emoji_string += f" *{autos:+}*"

    return emoji_string


def __should_double(command: dict, spec: bool) -> bool:
    """
    Determine whether 10s on a roll should count as double successes.
    Args:
        command (dict): The command dictionary comprising user syntax and guild settings
        spec (bool): Whether the roll has a specialty applied
    Returns (bool): True if rolled 10s should count as two successes
    """
    if command["never_double"]:
        return False
    if command["always_double"] or spec:
        return True
    return False


def __explosion_target(command: dict, spec: bool) -> int:
    """
    Determine the threshold at which rolls should explode. If they should never
    explode, it returns an unrollable number.
    Args:
        command (dict): The command dictionary comprising user syntax and guild settings
        spec (bool): Whether the roll has a specialty applied
    Returns (bool): True if rolled 10s should explode (be rolled again)
    """
    if command["xpl_always"]:
        return 10
    if command["xpl_spec"] and spec:
        return 10
    return 11 # An unreachable explosion target means no roll will ever explode
