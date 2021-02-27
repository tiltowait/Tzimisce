"""A class for performing pool-based rolls and determining number of successes."""

from . import Traditional

class Pool:
    """Provides facilities for pool-based rolls."""

    # pylint: disable=too-many-arguments
    # We don't have a choice here.

    def __init__(self, pool, difficulty, will, spec, autos):
        self.difficulty = difficulty
        self.will = will
        self.spec = spec
        self.autos = autos
        self.dice = sorted(Traditional.roll(pool, 10), reverse=True)

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

    @property
    def formatted(self):
        """
        Use Markdown formatting on the rolls.
          * Cross out failures.
          * Bold and cross out ones.
          * Bold tens if a specialty is in use.
        """
        formatted = []
        for roll in self.dice:
            if roll == 1:
                formatted.append(f"~~**{roll}**~~")
            elif roll < self.difficulty:
                formatted.append(f"~~{roll}~~")
            elif roll == 10 and self.spec:
                formatted.append(f"**{roll}**")
            else:
                formatted.append(str(roll))

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

        for roll in self.dice:
            if roll >= self.difficulty:
                suxx += 1
                if roll == 10 and self.spec:
                    suxx += 1
            elif roll == 1:
                fails += 1

        # Three possible results:
        #   * Botch
        #   * Failure
        #   * Success
        # If using Willpower, there's always one guaranteed success.
        if not self.will and fails > 0 and suxx == 0:  # Botch
            return -fails

        suxx = suxx - fails
        suxx = 0 if suxx < 0 else suxx
        if self.will:
            suxx += 1

        return suxx
