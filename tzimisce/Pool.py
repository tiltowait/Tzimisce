import random
from tzimisce import PlainRoll

class Pool:
    def __init__(self):
        self.formatted = []
        self.successes = 0

    #
    # Roll a specific die a number of times and return the results as an array.
    #
    def roll(self, pool, difficulty, wp, spec, autos):
        pool = int(pool)
        raw = sorted(PlainRoll.roll(pool, 10), reverse=True)
        self.formatted = self.__format_rolls(raw, difficulty, spec)
        self.successes = self.__count_successes(raw, difficulty, wp, spec, autos)

    #
    # Use Markdown formatting on the rolls.
    #   Cross out failures.
    #   Bold and cross out ones.
    #   Bold tens if a specialty is in use.
    #
    def __format_rolls(self, rolls, difficulty, spec):
        formatted = []
        for roll in rolls:
            if roll == 1:
                formatted.append('~~**{0}**~~'.format(roll))
            elif roll < difficulty:
                formatted.append('~~{0}~~'.format(roll))
            elif roll == 10 and spec:
                formatted.append('**{0}**'.format(roll))
            else:
                formatted.append('{0}'.format(roll))

        return formatted

    #
    # Sums the number of successes, taking into account Willpower use.
    #   Botch if no successes or willpower and failures > 0
    #   Failure if ones > successes
    #   Success if successes > ones
    #
    def __count_successes(self, rolls, difficulty, wp, spec, autos):
        suxx  = int(autos)
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
        #   # Success
        # If using Willpower, there's always one guaranteed success.
        if not wp and fails > 0 and suxx == 0: # Botch
            return -fails
        else:
            suxx = suxx - fails
            suxx = 0 if suxx < 0 else suxx
            if wp:
                suxx += 1

            return suxx
