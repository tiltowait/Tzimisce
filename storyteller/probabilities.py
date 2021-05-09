"""Calculates various probabilities and statistics about a given roll."""
# pylint: disable=c-extension-no-member

import math
from collections import namedtuple, defaultdict

SuccessfulPermutation = namedtuple("SuccessfulPermutation", ["tens", "successes", "ones"])
Probability = namedtuple("Probability", [
    "avg", "avg_spec", "prob", "prob_wp", "prob_spec", "prob_spec_wp", "fail", "fail_spec", "botch"
])

cached_probabilities = defaultdict(lambda: None)


def __multi_comb(total, *options) -> int:
    """Returns the number of permutations for a given combination. n! / (a! * b! * ... * z!)"""
    # The sum of options must equal the total
    options = list(options)
    options_sum = sum(options)

    if options_sum < total:
        options.append(total - options_sum)
    elif options_sum > total:
        raise ValueError("The sum of the options cannot exceed the total.")

    denominator = 1
    for option in options: # These must all be ints
        denominator *= math.factorial(option)

    return math.factorial(total) / denominator


def __successful_combinations(pool, target, specialty) -> list:
    """Returns all possible successful combinations for a given dice pool."""
    combinations = []

    for suxx in range(0, pool + 1):
        # Calculate the minimum number of tens required to reach the target
        min_tens = math.ceil((target - suxx) / 2)
        if min_tens < 0:
            min_tens = 0
        max_tens = pool - suxx

        for tens in range(min_tens, max_tens + 1):
            # Calculate the max number of ones allowed
            t_ss = suxx + tens
            if specialty:
                t_ss += tens # Tens only count for double successes in a specialty

            remaining_dice = pool - (suxx + tens)
            margin = t_ss - target
            max_ones = margin if margin <= remaining_dice else remaining_dice

            for ones in range(0, max_ones + 1):
                combinations.append(SuccessfulPermutation(tens, suxx, ones))

    return combinations


def __success_probability(pool, difficulty, target, specialty) -> float:
    """Returns the probability that a given roll is successful (with spec)."""
    combinations = __successful_combinations(pool, target, specialty)
    p_suxx = (10 - difficulty) / 10
    p_fail = (difficulty - 2) / 10

    running_prob = 0
    for comb in combinations:
        tens = comb.tens
        suxx = comb.successes
        ones = comb.ones
        fails = pool - tens - suxx - ones

        ncr = __multi_comb(pool, comb.tens, comb.successes, comb.ones, fails)
        running_prob += ncr * pow(.1, tens) * pow(p_suxx, suxx) * pow(.1, ones) * pow(p_fail, fails)

    return running_prob


def __botch_probability(pool, difficulty) -> float:
    """Returns the likelihood of a botch for a given roll."""
    if pool == 1:
        return .1

    p_suxx = (11 - difficulty) / 10

    running_prob = 0
    for k in range(1, pool):
        comb = __multi_comb(pool, k)
        running_prob += comb * pow(0.1, k) * pow(0.9 - p_suxx, pool - k)

    running_prob += pow(0.1, pool)

    return running_prob


def __average_successes(pool, difficulty) -> tuple:
    """Returns the average successes for a given roll, both without and with specialties."""
    avg = pool * ((11 - difficulty) / 10) - pool * .1
    avg_spec = pool * ((11 - difficulty) / 10)

    return (avg, avg_spec)


def get_probabilities(pool, difficulty, target) -> Probability:
    """Returns a Probability object containing the statistics for a given roll."""
    # Check the cache first
    key = f"{pool} {difficulty} {target}"
    probability = cached_probabilities[key]
    if probability:
        return probability

    elements = []

    avg, avg_spec = __average_successes(pool, difficulty)
    elements.append(avg)
    elements.append(avg_spec)

    prob = __success_probability(pool, difficulty, target, False)
    prob_wp = __success_probability(pool, difficulty, target - 1, False) if target > 1 else 1
    prob_spec = __success_probability(pool, difficulty, target, True)
    prob_spec_wp = __success_probability(pool, difficulty, target - 1, True) if target > 1 else 1
    fail = 1 - __success_probability(pool, difficulty, 1, False)
    fail_spec = 1 - __success_probability(pool, difficulty, 1, True)
    botch = __botch_probability(pool, difficulty)

    elements.append(prob)
    elements.append(prob_wp)
    elements.append(prob_spec)
    elements.append(prob_spec_wp)
    elements.append(fail)
    elements.append(fail_spec)
    elements.append(botch)

    probability = Probability(*elements)

    # Add to cache
    cached_probabilities[key] = probability

    return probability
