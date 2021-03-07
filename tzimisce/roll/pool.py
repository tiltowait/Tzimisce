"""A class for performing pool-based rolls and determining number of successes."""

from collections import namedtuple
from . import traditional

class Pool:
    """Provides facilities for pool-based rolls."""

    Options = namedtuple("Options", ["pool", "diff", "autos", "wp", "spec", "no_botch"])

    # pylint: disable=too-many-arguments
    # We don't have a choice here.

    def __init__(self, options):
        self.difficulty = options.diff
        self.will = options.wp
        self.spec = options.spec
        self.autos = options.autos
        self.no_botch = options.no_botch
        self.dice = sorted(traditional.roll(options.pool, 10), reverse=True)

    @property
    def formatted_result(self):
        """Format the successes to something nice for people to read."""
        # Determine roll string
        successes = self.successes
        result_str = ""
        if successes > 0:
            result_str = f"{successes} success"
            if successes > 1:
                result_str += "es"
        elif successes == 0 or self.no_botch:
            result_str = "Failure"
        else:
            result_str = f"Botch: {successes}"

        return result_str

    @property
    def formatted_dice(self):
        """
        Use Markdown formatting on the rolls.
          * Cross out failures.
          * Bold and cross out ones.
          * Bold tens if a specialty is in use.
        """
        formatted = []
        for die in self.dice:
            if die == 1:
                formatted.append(f"~~**{die}**~~")
            elif die < self.difficulty:
                formatted.append(f"~~{die}~~")
            elif die == 10 and self.spec:
                formatted.append(f"**{die}**")
            else:
                formatted.append(str(die))

        formatted = ", ".join(formatted)
        if self.will:
            formatted += " *+WP*"
        if self.autos > 0:
            formatted += f" *+{self.autos}*"

        return formatted

    @property
    def successes(self):
        """
        Sums the number of successes, taking into account Willpower use.
          * Botch if no successes or willpower and failures > 0
          * Failure if ones > successes
          * Success if successes > ones
        """
        suxx = self.autos
        fails = 0

        for die in self.dice:
            if die >= self.difficulty:
                suxx += 1
                if die == 10 and self.spec:
                    suxx += 1
            elif die == 1:
                fails += 1

        # Three possible results:
        #   * Botch
        #   * Failure
        #   * Success
        # If using Willpower, there's always one guaranteed success.
        if not self.will and fails > 0 and suxx == 0 and not self.no_botch:  # Botch
            return -fails

        suxx = suxx - fails
        suxx = 0 if suxx < 0 else suxx
        if self.will:
            suxx += 1

        if self.no_botch and suxx < 0:
            suxx = 0

        return suxx
