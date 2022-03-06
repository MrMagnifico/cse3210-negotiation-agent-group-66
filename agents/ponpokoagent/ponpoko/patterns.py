from enum import Enum
from math import cos
from math import sin
from math import tan
from operator import add
from operator import mul
from operator import pow
from operator import sub
from random import randint
from random import sample
from random import uniform


class PatternGeneratorType(Enum):
    # Use the patterns defined in the PonPokoAgent paper
    Standard = 1

    # Use opponent matching to get different patterns
    Opponent = 2

    # Randomly generate the values for the patterns.
    Random = 3

    # Randomly generate values and functions according to mutation principles.
    Mutation = 4

    # Only use the mutation principles.
    Operation = 5


# === Pattern Generation Magic ===
def _generate_value(a, b, op, trig):

    if op == sub:
        return lambda t: 1.0 - a * t - abs(trig(b * t))
    elif op == add:
        return lambda t: 1.0 - a * t + abs(trig(b * t))
    else:
        return lambda t: 1.0 - op(a * t, abs(trig(b * t)))


def _generate_pattern(one,
                      two,
                      op_one=sub,
                      op_two=sub,
                      trig_one=sin,
                      trig_two=sin):
    """Generates a pattern based on the algoriths described in the ANAC 2017 paper."""
    a, b = one
    c, d = two

    def inner(t: float, iftime: float):
        v = _generate_value(a, b, op_one, trig_one)(t)
        w = _generate_value(c, d, op_two, trig_two)(t)
        return (v, w)

    return inner


def _mutate_pattern(one, two):
    operators = [mul, sub, add, pow]
    trigops = [sin, cos, tan]

    op_one = sample(operators, 1)[0]
    op_two = sample(operators, 1)[0]
    trig_one = sample(trigops, 1)[0]
    trig_two = sample(trigops, 1)[0]

    print(
        f"1.0 - {one[0]}t {op_one.__name__} abs({trig_one.__name__}({one[1]}t))"
    )
    print(
        f"1.0 - {two[0]}t {op_two.__name__} abs({trig_two.__name__}({two[1]}t))"
    )

    return _generate_pattern(one, two, op_one, op_two, trig_one, trig_two)


# === Patterns which are used === #
pattern_values = [((0.1, 0), (0.1, 40)), ((0.1, 0), (0.22, 0)),
                  ((0.1, 0), (0.15, 20)), ((0.15, 20), (0.21, 20))]
pattern_1 = _generate_pattern(pattern_values[0][0], pattern_values[0][1])
pattern_2 = _generate_pattern(pattern_values[1][0], pattern_values[1][1])
pattern_3 = _generate_pattern(pattern_values[2][0], pattern_values[2][1])
pattern_5 = _generate_pattern(pattern_values[3][0],
                              pattern_values[3][1],
                              op_one=mul,
                              op_two=mul)

hardliner_pattern_1 = _generate_pattern((0.01, 0), (0.01, 25))

conceder_pattern_1 = _generate_pattern((0.25, 0), (0.25, 25))


def pattern_4(t: float, iftime: float):
    """Applies the fourth pattern."""
    highest_util = 1.0 - 0.05 * t
    if iftime <= 0.99:
        lowest_util = 1.0 - 0.1 * t
    else:
        lowest_util = 1.0 - 0.3 * t
    return (highest_util, lowest_util)


class Patterns:
    """An iterator which generates different patterns."""

    _patterns = [pattern_1, pattern_2, pattern_3, pattern_5]
    _conceder_patterns = [conceder_pattern_1]
    _hardliner_patterns = [hardliner_pattern_1]
    _opponent = ""

    def __init__(self, type_):
        """Creates the pattern generator."""
        self._index = 0
        self._type = type_

    def __next__(self):
        """Generates a function which returns a pair with the utility value."""
        if self._type == PatternGeneratorType.Standard:
            self._index = randint(0, len(self._patterns) - 1)
            return self._patterns[self._index]
        elif self._type == PatternGeneratorType.Opponent:
            if self._opponent == "hardliner":
                self._index = randint(0, len(self._conceder_patterns) - 1)
                return self._conceder_patterns[self._index]
            elif self._opponent == "conceder":
                self._index = randint(0, len(self._hardliner_patterns) - 1)
                return self._hardliner_patterns[self._index]
            else:
                self._index = randint(0, len(self._patterns) - 1)
                return self._patterns[self._index]
        elif self._type == PatternGeneratorType.Random:
            one = (uniform(0.01, 0.15), randint(0, 20))
            two = (uniform(0.01, 0.35), randint(0, 80))
            print(one, two)
            return _generate_pattern(one, two)
        elif self._type == PatternGeneratorType.Mutation:
            one = (uniform(0.01, 0.15), randint(0, 20))
            two = (uniform(0.01, 0.35), randint(0, 80))
            return _mutate_pattern(one, two)
        elif self._type == PatternGeneratorType.Operation:
            self._index = randint(0, len(self._patterns) - 1)
            a, b = pattern_values[self._index]
            return _mutate_pattern(a, b)
