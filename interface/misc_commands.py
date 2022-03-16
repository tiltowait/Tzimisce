"""misc_commands.py - A cog that has miscellaneous commands."""

import discord
from discord.commands import slash_command, Option
from discord.ext import commands
from discord.ui import View, Button

import storyteller


class _LinkView(View):
    """A view with support links."""

    def __init__(self):
        super().__init__()
        self.add_item(Button(label="Documentation", url="https://www.storyteller-bot.com/#/"))
        self.add_item(Button(label="Support", url="https://discord.gg/QHnCdSPeEE"))
        self.add_item(Button(label="Patreon", url="https://www.patreon.com/tiltowait"))


class MiscCommands(commands.Cog):
    """Cog for miscellaneous commands."""

    @slash_command(name="help")
    async def __help(self, ctx):
        """Displays the basic syntax and a link to the full help file."""
        embed = storyteller.engine.help_embed("/mm syntax:")
        await ctx.respond(embed=embed, view=_LinkView())


    @slash_command()
    async def coinflip(self, ctx):
        """Flip a coin!"""
        coin = storyteller.roll.traditional.roll(1, 2)[0]
        if coin == 1:
            coin = "**Heads!**"
        else:
            coin = "**Tails!**"

        await ctx.respond(coin)


    @slash_command()
    async def stats(
        self,
        ctx: discord.ApplicationContext,
        syntax: Option(
            str,
            "Format: POOL DIFFICULTY TARGET"
        ),
    ):
        """Calculate the probability of a given roll outcome."""
        usage = "Expected arguments: <pool> <difficulty> <target>"
        try:
            args = syntax.split()
            pool = int(args.pop(0))
            diff = int(args.pop(0))
            target = 1

            if len(args) > 0:
                target = int(args.pop(0))

            # Check our constraints
            if not 1 <= pool <= 30:
                raise ValueError("Error! Pool must be between 1-30!")

            if not 2 <= diff <= 10:
                raise ValueError("Error! Difficulty must be between 2-10!")

            if not 1 <= target <= (pool * 2):
                raise ValueError("Error! Success target must be between 1 and twice your pool!")

            prob = storyteller.probabilities.get_probabilities(pool, diff, target)

            # Properly pluralize "successes", when applicable
            success = "success"
            if target > 1:
                success += "es"

            title = f"Statistics for {target} {success} at {pool} v {diff}"
            embed = discord.Embed(title=title)

            standard = f"**Average successes:** {prob.avg:.3}\n"
            standard += f"**{target}+ {success}:** {prob.prob:.3%}\n"
            standard += f"**Using Willpower:** {prob.prob_wp:.3%}\n"
            standard += f"**Total Failure:** {prob.fail:.3%}\n"
            standard += f"**Botch:** {prob.botch:.3%}"

            spec = f"**Average successes:** {prob.avg_spec:.3}\n"
            spec += f"**{target}+ {success}:** {prob.prob_spec:.3%}\n"
            spec += f"**Using Willpower:** {prob.prob_spec_wp:.3%}\n"
            spec += f"**Total Failure:** {prob.fail_spec:.3%}\n"
            spec += f"**Botch:** {prob.botch:.3%}"

            embed.add_field(name="Standard Roll", value=standard, inline=False)
            embed.add_field(name="With Specialty", value=spec, inline=False)

            await ctx.respond(embed=embed)
        except IndexError:
            await ctx.respond(usage, ephemeral=True)
        except ValueError as error:
            await ctx.respond(f"{error}\n{usage}", ephemeral=True)

        # Log statistics
        if ctx.guild:
            storyteller.engine.statistics.increment_stats_calculated(ctx.guild)


def setup(bot):
    """Setup the command interface."""
    bot.add_cog(MiscCommands(bot))
