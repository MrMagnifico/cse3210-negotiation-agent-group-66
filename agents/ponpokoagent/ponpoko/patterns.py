from math import sin
from operator import add
from operator import mul
from operator import sub
from random import randint
from random import random


# === Pattern Generation Magic ===
def _generate_value(a, b, op):
    if op == sub:
        return lambda t: 1.0 - a * t - abs(sin(b * t))
    elif op == add:
        return lambda t: 1.0 - a * t + abs(sin(b * t))
    else:
        return lambda t: 1.0 - op(a * t, abs(sin(b * t)))


def _generate_pattern(one, two, op_one=sub, op_two=sub):
    """Generates a pattern based on the algoriths described in the ANAC 2017 paper."""
    a, b = one
    c, d = two

    def inner(t: float, iftime: float):
        return (_generate_value(a, b,
                                op_one)(t), _generate_value(c, d, op_two)(t))

    return inner


pattern_1 = _generate_pattern((0.1, 0), (0.1, 40))
pattern_2 = _generate_pattern((0.1, 0), (0.22, 0))
pattern_3 = _generate_pattern((0.1, 0), (0.15, 20))
pattern_5 = _generate_pattern((0.15, 20), (0.21, 20), op_one=mul, op_two=mul)


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
    _conceder_patterns = []
    _hardliner_patterns = []
    _opponent = ""

    def __init__(self, random):
        """Creates the pattern generator."""
        self._random = random
        self._index = 0

    def __next__(self):
        """Generates a function which returns a pair with the utility values."""
        if self._random:
            return _generate_pattern((random(), random()),
                                     (random(), random()))
        if self._opponent == "conceder":
            self._index = randint(0, len(self._conceder_patterns) - 1)
            self._conceder_patterns[self._index]
        elif self._opponent == "hardliner":
            self._index = randint(0, len(self._hardliner_patterns) - 1)
            self._hardliner_patterns[self._index]
        
        self._index = randint(0, len(self._patterns) - 1)
        return self._patterns[self._index]
