import random

class Pool:
    def __init__(self):
        self.raw = []
        self.formatted = []
        self.result_str = []
        self.successes = 0

    #
    # Roll a specific die a number of times and return the results as an array.
    #
    def roll(self, pool, difficulty, wp, spec):
        pool = int(pool)
        self.raw = sorted([random.randint(1, 10) for _ in range(pool)], reverse=True)
        self.formatted = self.__format_rolls(self.raw, difficulty, spec)
        self.result_str = self.__count_successes(self.raw, difficulty, wp, spec)

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
    def __count_successes(self, rolls, difficulty, wp, spec):
        suxx  = 0
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
            self.successes = -fails
            return 'Botch: {0}'.format(-fails)
        else:
            suxx = suxx - fails
            suxx = 0 if suxx < 0 else suxx
            if wp:
                suxx += 1

            self.successes = suxx

            if suxx == 0:
                return 'Failure'
            else:
                output = '{0} success'.format(suxx)
                if suxx > 1:
                  output += 'es' # Properly pluralize!

                if wp:
                  output += ' (inc WP)'

                return output
