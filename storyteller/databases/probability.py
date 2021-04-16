"""probability.py - Defines a database and probability simulator for dice rolls."""

from random import randint # Using random instead of secrets for speed
from collections import namedtuple
from .base import Database

Probability = namedtuple("Probability", [
    "avg", "avg_spec", "prob", "prob_spec", "fail", "fail_spec", "botch"
])

class ProbabilityDB(Database):
    """Maintains and populates a database table for roll probabilities."""

    def __init__(self):
        super().__init__()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Probabilities(
                key Text PRIMARY KEY,
                avg DOUBLE PRECISION,
                avg_spec DOUBLE PRECISION,
                prob DOUBLE PRECISION,
                prob_spec DOUBLE PRECISION,
                fail DOUBLE PRECISION,
                fail_spec DOUBLE PRECISION,
                botch DOUBLE PRECISION
            );
            """
        )

    def __probabilities(self, pool=int, diff=int, target=int):
        """Returns the probabilities matching the parameters."""
        key = f"{pool} {diff} {target}"
        query = "SELECT * FROM Probabilities WHERE Key=%s;"
        self._execute(query, key)

        result = self.cursor.fetchone()
        if result is None:
            return None

        result = list(result)
        del result[0] # Remove "key"

        prob = Probability(*result)
        return prob


    def __store_probabilities(self, key: str, stats: list):
        """Stores the given probabilities."""
        query = "INSERT INTO Probabilities VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
        self._execute(query, key, *stats)


    def is_cached(self, pool=int, diff=int, target=int) -> bool:
        """Returns true if statistics matching the parameters minus one exist in the database."""
        prob = self.__probabilities(pool, diff, target)
        prob_wp = self.__probabilities(pool, diff, target - 1)

        return prob is not None and prob_wp is not None


    def get_probabilities(self, pool=int, diff=int, target=int) -> tuple:
        """Returns or calculates the probabilities for a roll."""
        prob = self.__probabilities(pool, diff, target)
        prob_wp = self.__probabilities(pool, diff, target - 1)

        if not prob:
            key = f"{pool} {diff} {target}"
            prob = calculate_probabilities(pool, diff, target)
            self.__store_probabilities(key, prob)
            prob = Probability(*prob)

        if not prob_wp:
            key = f"{pool} {diff} {target - 1}"
            prob_wp = calculate_probabilities(pool, diff, target - 1)
            self.__store_probabilities(key, prob_wp)
            prob_wp = Probability(*prob_wp)

        return (prob, prob_wp)


def calculate_probabilities(pool=int, diff=int, target=int) -> list:
    """Calculate roll probabilities."""
    # pylint: disable=too-many-locals

    trials = 1000000

    successful_runs = 0
    successful_spec_runs = 0
    failed_runs = 0
    failed_spec_runs = 0
    botched_runs = 0

    for _ in range(0, trials):
        tens = 0
        successes = 0
        ones = 0
        for _ in range(0, pool):
            die = randint(1, 10)

            if die == 10:
                tens += 1
            elif die >= diff:
                successes += 1
            elif die == 1:
                ones += 1

        # Calculate results
        successes = tens + successes
        net = successes - ones

        spec_successes = successes + tens
        spec_net = spec_successes - ones

        # Check botch
        if net < 0 and successes == 0:
            botched_runs += 1
            continue

        # Check failure
        if net <= 0:
            failed_runs += 1

        if spec_net <= 0:
            failed_spec_runs += 1

        # Check success
        if net >= target:
            successful_runs += 1

        if spec_net >= target:
            successful_spec_runs += 1

    # Calculate final probabilities
    stats = []

    # Averages
    avg_spec = pool * ((11 - diff) / 10)
    avg = pool * ((11 - diff) / 10) - pool * 0.1
    stats.append(avg)
    stats.append(avg_spec)

    # Successful
    prob = successful_runs / trials
    prob_spec = successful_spec_runs / trials
    stats.append(prob)
    stats.append(prob_spec)

    # Failure
    fail = failed_runs / trials
    fail_spec = failed_spec_runs / trials
    stats.append(fail)
    stats.append(fail_spec)

    # Botch
    botch = botched_runs / trials
    stats.append(botch)

    return stats
