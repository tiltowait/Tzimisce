"""A class for performing pool-based rolls and determining number of successes."""

from . import traditional

class Pool:
    """Provides facilities for pool-based rolls."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, pool, diff, autos, wp, double, no_botch, nullify_ones, explode, wp_c):
        # pylint: disable=too-many-arguments
        self.difficulty = diff
        self.should_double = double
        self.will = wp
        self.autos = autos
        self.no_botch = no_botch
        self.nullify_ones = nullify_ones
        self.should_explode = explode
        self.wp_cancelable = wp_c
        self.dice = self.__roll(pool)

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
            if die == 1 and not (self.nullify_ones and self.no_botch):
                formatted.append(f"~~***{die}***~~")
            elif die < self.difficulty:
                formatted.append(f"~~{die}~~")
            elif die == 10 and self.should_double:
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
    def successes(self) -> int:
        """
        Sums the number of successes, taking into account Willpower use.
          * Botch if no successes or willpower and failures > 0
          * Failure if ones > successes
          * Success if successes > ones
        """
        suxx = 1 if self.will else 0
        fails = 0
        if self.autos > 0:
            suxx += self.autos
        elif self.autos < 0:
            fails -= self.autos # Auto-failures are negative

        for die in self.dice:
            if die >= self.difficulty:
                suxx += 1
                if die == 10 and self.should_double:
                    suxx += 1
            elif die == 1 and not (self.nullify_ones and self.no_botch):
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
        if suxx == 0 and self.will and not self.wp_cancelable:
            suxx += 1

        if self.no_botch and suxx < 0:
            suxx = 0

        return suxx

    def __roll(self, pool) -> list:
        """Roll the dice!"""

        # Exploding dice: on a ten, roll an additional die. This is recursive
        if self.should_explode:
            dice = []
            for _ in range(pool):
                die = traditional.roll(1, 10)[0]
                while die == 10:
                    dice.append(die)
                    die = traditional.roll(1, 10)[0]
                dice.append(die)

            return sorted(dice, reverse=True)

        # Normal, non-exploding rolling
        return sorted(traditional.roll(pool, 10), reverse=True)

    @property
    def dice_emoji_names(self):
        """Returns the emoji names based on the dice, difficulty, spec, etc."""
        names = []
        for die in self.dice:
            name = ""
            if die >= self.difficulty:
                name = f"s{die}"
            elif die > 1 or (self.nullify_ones and self.no_botch):
                name = f"f{die}"
            else:
                name = "b1"

            if die == 10 and self.should_double:
                name = f"s{name}"

            names.append(name)
        return names
