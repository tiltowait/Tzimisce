"""parse/initiative.py - Parses user input when invoking minit."""

import argparse
import io
from contextlib import redirect_stderr

import storyteller.engine # pylint: disable=cyclic-import
import storyteller.initiative
from storyteller.initiative import InitiativeManager
from .response import Response


def initiative(ctx, mod, args) -> Response:
    """Parses minit input and returns appropriate results."""
    prefix = storyteller.settings.get_prefixes(ctx.guild)[0]
    usage = "**Initiative Manager Commands**\n"
    usage += f"`{prefix}i` — Show initiative table (if one exists in this channel)\n"
    usage += f"`{prefix}i <mod> <character>` — Roll initiative (character optional)\n"
    usage += f"`{prefix}i dec <action> [-n character] [-c N]` — Declare a character action\n"
    usage += f"`{prefix}i remove [character]` — Remove initiative (character optional)\n"
    usage += f"`{prefix}i reroll` — Reroll all initiatives\n"
    usage += f"`{prefix}i clear` — Clear the table"

    manager = storyteller.initiative.get_table(ctx.channel.id)
    response = Response(Response.INITIATIVE)

    if not mod: # Not rolling
        if manager:
            embed = storyteller.engine.build_embed(
                title="Initiative", description=str(manager),
                footer="Commands: remove | clear | reroll | declare",
                fields=[]
            )

            content = None
            if ctx.invoked_with == "reroll":
                content = "Rerolling initiative!"
            response.embed = embed
            response.content = content
            return response

        response.content = usage
        return response

    # Rolling initiative
    try:
        is_modifier = mod[0] == "-" or mod[0] == "+"
        mod = int(mod)

        # Add init to manager
        if not manager:
            manager = InitiativeManager()
        character_name = args or ctx.author.display_name

        init = None
        if not is_modifier:
            init = manager.add_init(character_name, mod)
            storyteller.initiative.add_table(ctx.channel.id, manager)
        else:
            init = manager.modify_init(character_name, mod)
            if not init:
                response.content = f"{character_name} has no initiative to modify!"
                return response

        title = f"{character_name}'s Initiative"

        entry = "entries" if manager.count > 1 else "entry"
        footer = f"{manager.count} {entry} in table. To see initiative: {prefix}i"

        if is_modifier:
            footer = f"Initiative modified by {mod:+}.\n{footer}"

        embed = storyteller.engine.build_embed(
            title=title, description=str(init), fields=[], footer=footer
        )

        storyteller.initiative.set_initiative(
            ctx.guild.id, ctx.channel.id, character_name, init.mod, init.die
        )
        storyteller.engine.statistics.increment_initiative_rolls(ctx.guild.id)

        response.embed = embed
        return response
    except ValueError:
        response.content = usage
        return response

def initiative_removal(ctx, args):
    """Removes a character from initiative, if possible, and returns a status response."""
    manager = storyteller.initiative.get_table(ctx.channel.id)
    response = Response(Response.INITIATIVE)

    if manager:
        character = args or ctx.author.display_name
        removed = manager.remove_init(character)
        if removed:
            storyteller.initiative.remove_initiative(ctx.channel.id, character)
            message = f"Removed {character} from initiative!"

            if manager.count == 0:
                storyteller.initiative.remove_table(ctx.channel.id)
                message += "\nNo characters left in initiative. Clearing table."

            response.content = message
        else:
            response.content = f"Unable to remove {character}; not in initiative!"
    else:
        response.content = "Initiative isn't running in this channel!"

    return response

# Initiative Declarations

parser = argparse.ArgumentParser(exit_on_error=False)
parser.add_argument("action", nargs="*", default=None)
parser.add_argument("-n", "--name", nargs="*", dest="character")
parser.add_argument("-c", "--celerity", nargs="?", type=int, const=1)

def initiative_declare(ctx, args):
    """Declares an initiative action, if possible."""
    try:
        parsed = None
        stream = io.StringIO()
        with redirect_stderr(stream): # Redirect argparse's error message
            parsed = parser.parse_args(args)

        character = ctx.author.display_name
        if parsed.character:
            character = " ".join(parsed.character)

        manager = storyteller.initiative.get_table(ctx.channel.id)
        if not parsed.celerity:
            if not parsed.action:
                raise SyntaxError("You need to supply an action!")

            action = " ".join(parsed.action)
            if not manager.declare_action(character, action):
                raise NameError(character)

            storyteller.initiative.set_initiative_action(
                ctx.channel.id, character, action
            )
        else:
            if not manager.has_character(character):
                raise NameError(character)

            for _ in range(parsed.celerity):
                manager.add_celerity(character)

    except AttributeError:
        raise SyntaxError("Initiative isn't set in this channel!") from None
    except NameError:
        raise SyntaxError(f"{character} isn't in the initiative table!") from None
    except (SystemExit, argparse.ArgumentError):
        raise SyntaxError("Usage: `/mi dec <action> [-n character] [--celerity N]`") from None
