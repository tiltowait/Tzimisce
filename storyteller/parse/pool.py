"""pool.py - Performs pool-based rolls for the user."""

import re

import discord
from storyteller import roll, engine # pylint: disable=cyclic-import
from .response import Response

__poolx = re.compile(
    r"^(?P<pool>-?\d+)[\s@]?(?P<difficulty>\d+)?\s?(?P<auto>[+-]?\d+)?(?: (?P<specialty>\D[^#]*))?$"
)

# Colors help show, at a glance, if a roll was successful
EXCEPTIONAL_COLOR = 0x00FF00
SUCCESS_COLOR = 0x0DC06B
MARGINAL_COLOR = 0x14A1A0
FAIL_COLOR = 0X777777
BOTCH_COLOR = 0XfF0000


async def pool(ctx, command) -> Response:
    """Determine if a roll is appropriate, and roll it."""
    pool_command = __poolx.match(command["syntax"])
    response = None
    if pool_command:
        command.update(pool_command.groupdict())
        send = __pool_roll(ctx, command)

        if isinstance(send, discord.Embed):
            response = Response(Response.POOL, embed=send)
        else: # It's a string
            response = Response(Response.POOL, content=send)

    return response

def is_valid_pool(syntax: str) -> bool:
    """Determines whether the syntax is a valid pool roll."""
    return __poolx.match(syntax) is not None

def __pool_roll(ctx, command):
    """
    A pool-based VtM roll. Returns the results in a pretty embed.
    Does not check that difficulty is 1 or > 10.
    """
    will = command["will"]
    compact = command["compact"]
    no_botch = command["no_botch"]
    dice_pool = int(command["pool"])

    if not 1 <= dice_pool <= 100:
        return f"Sorry, pools must be between 1 and 100. *(Input: {dice_pool})*"

    # Difficulty must be between 2 and 10. If it isn't supplied, go with
    # the default value of 6.
    difficulty = int(command["difficulty"] or command["default_diff"])
    if not 2 <= difficulty <= 10:
        return f"Whoops! Difficulty must be between 2 and 10. *(Input: {difficulty})*"

    title = f"Pool {dice_pool}, diff. {difficulty}"

    # Sometimes, a roll may have auto-successes that can be canceled by 1s.
    autos = int(command["auto"] or 0)
    if autos != 0:
        title += f", {__pluralize_autos(autos)}"

    # Let the user know if we aren't allowing botches
    if no_botch:
        title += ", no botch"

    specialty = command["specialty"] # Doubles 10s if set
    should_double = __should_double(command, specialty is not None)
    should_explode = __should_explode(command, specialty is not None)

    # Perform rolls, format them, and figure out how many successes we have
    results = roll.Pool(
        dice_pool, difficulty, autos, will, should_double,
        no_botch, command["nullify_ones"], should_explode, command["wp_cancelable"]
    )
    comment = command["comment"]

    # Compact formatting
    if compact:
        return __build_compact(results, specialty, comment)

    # If not compact, put the results into an embed
    return __build_embed(ctx, command["override"], results, specialty, will, autos, title, comment)

def __build_embed(ctx, override, results, specialty, will, autos, title, comment):
    """Builds an embed for the roll results."""
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

    if ctx.channel.permissions_for(ctx.me).external_emojis and len(results.dice) <= 40:
        names = results.dice_emoji_names
        emojis = __emojify_dice(ctx, names, will, autos)
        fields.append(("Dice", emojis, True))
    else:
        fields.append(("Dice", results.formatted_dice, True))

    if specialty:
        fields.append(("Specialty", specialty, True))

    fields.append(("Result", results.formatted_result, False))

    return engine.build_embed(
        author=ctx.author, header=title, color=color, fields=fields,
        footer=comment
    )

def __build_compact(results, specialty, comment):
    """Builds a compact result string for the roll."""
    compact_string = ""

    if comment:
        compact_string += f"> {comment}\n\n"

    compact_string += f"{results.formatted_dice}"
    if specialty:
        compact_string += f"   ({specialty})"

    compact_string += f"\n**{results.formatted_result}**"

    return compact_string

def __pluralize_autos(autos):
    """Pluralize 'N auto(s)' as needed"""
    string = f"{autos:+} success"
    if abs(autos) > 1:
        string += "es"

    return string


# Emoji stuff

# Dice are programmatically converted to their emoji name. The name is composed of
# two or three elements: specialty/success/failure/botch + the number. A successful 6
# becomes 's6', whereas a failing 2 becomes 'f2'. 'ss10' means a specialty 10, and
# 'b1' means a botching 1.

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

def __emojify_dice(ctx, names, willpower, autos) -> str:
    """Returns an Emoji constructed from the emojidict dictionary."""
    emojis = []
    for name in names:
        emoji = emojidict[name]
        if isinstance(emoji, int):
            emoji = ctx.bot.get_emoji(emoji)
            emojidict[name] = emoji # Cache the emoji rather than the id

        emojis.append(emoji)

    emojis = list(map(str, emojis))
    emoji_string = " ".join(emojis)

    if willpower:
        emoji_string += " *+WP*"
    if autos != 0:
        emoji_string += f" *{autos:+}*"

    return emoji_string

def __should_double(command: dict, spec: bool) -> bool:
    """Determines whether 10s on a roll should count as double successes."""
    if command["never_double"]:
        return False
    if command["always_double"] or spec:
        return True
    return False

def __should_explode(command: dict, spec: bool) -> bool:
    """Determines whether 10s on a roll should explode."""
    if command["xpl_always"]:
        return True
    if command["xpl_spec"] and spec:
        return True
    return False
