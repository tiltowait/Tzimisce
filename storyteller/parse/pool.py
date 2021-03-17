"""pool.py - Performs pool-based rolls for the user."""

import re

import discord
from storyteller import roll, engine # pylint: disable=cyclic-import
from .response import Response

__poolx = re.compile(
    r"^(?P<pool>-?\d+)[\s@]?(?P<difficulty>\d+)?[\s\+]?(?P<auto>\d+)?(?: (?P<specialty>\D[^#]*))?$"
)

# Colors help show, at a glance, if a roll was successful
EXCEPTIONAL_COLOR = 0x00FF00
SUCCESS_COLOR = 0x0DC06B
MARGINAL_COLOR = 0x14A1A0
FAIL_COLOR = 0X777777
BOTCH_COLOR = 0XfF0000


async def parse(ctx, command, mentioning) -> Response:
    """Determine if a roll is appropriate, and roll it."""
    pool = __poolx.match(command["syntax"])
    response = None
    if pool:
        command.update(pool.groupdict())
        send = __pool_roll(ctx, command)

        if isinstance(send, discord.Embed):
            response = Response(Response.POOL, embed=send)
            if mentioning:
                response.content = ctx.author.mention
        else: # It's a string
            if mentioning:
                send = f"{ctx.author.mention}: {send}"
            response = Response(Response.POOL, content=send)

    return response

def __pool_roll(ctx, command):
    """
    A pool-based VtM roll. Returns the results in a pretty embed.
    Does not check that difficulty is 1 or > 10.
    """
    will = command["will"]
    compact = command["compact"]
    no_botch = command["no_botch"]
    pool = int(command["pool"])

    if pool < 1 or pool > 100:
        return f"Sorry, pools must be between 1 and 100. *(Input: {pool})*"

    # Difficulty must be between 2 and 10. If it isn't supplied, go with
    # the default value of 6.
    difficulty = int(command["difficulty"] or command["default_diff"])
    if difficulty > 10 or difficulty < 2:
        return f"Whoops! Difficulty must be between 2 and 10. *(Input: {difficulty})*"

    title = f"Pool {pool}, diff. {difficulty}"

    # Sometimes, a roll may have auto-successes that can be canceled by 1s.
    autos = int(command["auto"] or "0")
    if autos > 0:
        title += f", +{__pluralize_autos(autos)}"

    # Let the user know if we aren't allowing botches
    if no_botch:
        title += ", no botch"

    specialty = command["specialty"] # Doubles 10s if set
    should_double = specialty is not None or command["always_double"]

    # Perform rolls, format them, and figure out how many successes we have
    results = roll.Pool(
        roll.Pool.Options(
            pool, difficulty, autos, will, should_double,
            no_botch, command["no_double"], command["nullify_ones"], command["xpl_always"],
            command["xpl_spec"]
        )
    )
    comment = command["comment"]

    # Compact formatting
    if compact:
        compact_string = ""

        if comment:
            compact_string += f"> {comment}\n\n"

        compact_string += f"{results.formatted_dice}"
        if specialty:
            compact_string += f"   ({specialty})"

        compact_string += f"\n**{results.formatted_result}**"

        return compact_string

    # If not compact, put the results into an embed

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
    if command["override"]:
        fields.append(("Macro override", command["override"], False))

    if ctx.channel.permissions_for(ctx.me).external_emojis and len(results.dice) <= 40:
        should_double = should_double and not command["no_double"]
        ones_botch = not command["nullify_ones"]
        names = emoji_names(results.dice, difficulty, should_double, ones_botch)
        fields.append(("Dice", dice_as_emojis(ctx, names), True))
    else:
        fields.append(("Dice", results.formatted_dice, True))

    if specialty:
        fields.append(("Specialty", specialty, True))

    fields.append(("Result", results.formatted_result, False))

    return engine.build_embed(
        author=ctx.author, header=title, color=color, fields=fields,
        footer=comment
    )

def __pluralize_autos(autos):
    """Pluralize 'N auto(s)' as needed"""
    string = f"{autos} auto"
    if autos > 1:
        string += "s"

    return string


# Emoji stuff

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

def dice_as_emojis(ctx, names) -> str:
    """Returns an Emoji constructed from the emojidict dictionary."""
    emojis = []
    for name in names:
        emoji_id = emojidict[name]
        emoji = ctx.bot.get_emoji(emoji_id)
        emojis.append(emoji)

    emojis = list(map(str, emojis))
    return " ".join(emojis)

def emoji_names(dice, diff, doubling, botching):
    """Returns the emoji names based on the dice, difficulty, spec, etc."""
    names = []
    for die in dice:
        name = ""
        if die >= diff:
            name = f"s{die}"
        elif die > 1 or not botching:
            name = f"f{die}"
        else:
            name = "b1"

        if die == 10 and doubling:
            name = f"s{name}"

        names.append(name)
    return names
