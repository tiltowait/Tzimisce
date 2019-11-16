'''A class for performing pool-based rolls and determining number of successes.'''

from tzimisce import PlainRoll

class Pool:
    '''Provides facilities for pool-based rolls.'''

    # pylint: disable=too-many-arguments
    # We don't have a choice here.

    def __init__(self):
        self.formatted = []
        self.successes = 0
        self.will = False

    def roll(self, pool, difficulty, will, spec, autos):
        '''Roll a specific die a number of times and return the results as an array.'''
        raw = sorted(PlainRoll.roll(int(pool), 10), reverse=True)
        self.formatted = self.__format_rolls(raw, difficulty, spec)
        self.successes = self.__count_successes(raw, difficulty, will, spec, autos)

    def formatted_count(self):
        '''Format the successes to something nice for people to read.'''
        # Determine roll string
        result_str = ''
        if self.successes > 0:
            result_str = '{} success'.format(self.successes)
            if self.successes > 1:
                result_str += 'es'

            if self.will:
                result_str += ' (inc. WP)'
        elif self.successes == 0:
            result_str = 'Failure'
        else:
            result_str = 'Botch: {}'.format(self.successes)

        return result_str

    #
    #
    def __format_rolls(self, rolls, difficulty, spec):
        '''
        Use Markdown formatting on the rolls.
          * Cross out failures.
          * Bold and cross out ones.
          * Bold tens if a specialty is in use.
        '''
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

    def __count_successes(self, rolls, difficulty, will, spec, autos):
        '''
        Sums the number of successes, taking into account Willpower use.
          * Botch if no successes or willpower and failures > 0
          * Failure if ones > successes
          * Success if successes > ones
        '''
        self.will = will

        suxx = int(autos)
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
        if not will and fails > 0 and suxx == 0: # Botch
            return -fails

        suxx = suxx - fails
        suxx = 0 if suxx < 0 else suxx
        if will:
            suxx += 1

        return suxx
