"""A class for performing pool-based rolls and determining number of successes."""

from . import Traditional

class Pool:
    """Provides facilities for pool-based rolls."""

    # pylint: disable=too-many-arguments
    # We don't have a choice here.

    def __init__(self):
        self.formatted = ""
        self.successes = 0
        self.will = False

    def roll(self, pool, difficulty, will, spec, autos):
        """Roll a specific die a number of times and return the results as an array."""
        raw = sorted(Traditional.roll(pool, 10), reverse=True)
        self.formatted = ", ".join(self.__format_rolls(raw, difficulty, spec))
        if will:
            self.formatted += " *+WP*"
        if autos > 0:
            self.formatted += f" *+{autos}*"
        self.successes = self.__count_successes(raw, difficulty, will, spec, autos)

    @property
    def formatted_count(self):
        """Format the successes to something nice for people to read."""
        # Determine roll string
        result_str = ""
        if self.successes > 0:
            result_str = f"{self.successes} success"
            if self.successes > 1:
                result_str += "es"
        elif self.successes == 0:
            result_str = "Failure"
        else:
            result_str = f"Botch: {self.successes}"

        return result_str

    def __format_rolls(self, rolls, difficulty, spec):
        """
        Use Markdown formatting on the rolls.
          * Cross out failures.
          * Bold and cross out ones.
          * Bold tens if a specialty is in use.
        """
        formatted = []
        for roll in rolls:
            if roll == 1:
                formatted.append(f"~~**{roll}**~~")
            elif roll < difficulty:
                formatted.append(f"~~{roll}~~")
            elif roll == 10 and spec:
                formatted.append(f"**{roll}**")
            else:
                formatted.append(str(roll))

        return formatted

    def __count_successes(self, rolls, difficulty, will, spec, autos):
        """
        Sums the number of successes, taking into account Willpower use.
          * Botch if no successes or willpower and failures > 0
          * Failure if ones > successes
          * Success if successes > ones
        """
        self.will = will

        suxx = autos
        fails = 0

        for roll in rolls:
            if roll >= difficulty:
                suxx += 1
                if roll == 10 and spec:
                    suxx += 1
            elif roll == 1:
                fails += 1

        # Three possible results:
        #   * Botch
        #   * Failure
        #   * Success
        # If using Willpower, there's always one guaranteed success.
        if not will and fails > 0 and suxx == 0:  # Botch
            return -fails

        suxx = suxx - fails
        suxx = 0 if suxx < 0 else suxx
        if will:
            suxx += 1

        return suxx
