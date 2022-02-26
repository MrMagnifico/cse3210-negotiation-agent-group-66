from operator import sub, mul
from math import sin
from random import random, randint

def generate_pattern(one, two, op_one=sub, op_two=sub):
    a, b = one
    c, d = two
    
    def inner(t, iftime):
        high = 1.0 - op_one(a*t, abs(sin(b*t)))
        low = 1.0 - op_two(c*t, abs(sin(d*t)))
        return (high, low)
    
                        
    return inner

pattern_1 = generate_pattern((0.1, 0), (0.1, 40))
pattern_2 = generate_pattern((0.1, 0) , (0.22, 0))
pattern_3 = generate_pattern((0.05, 0), (0.15, 20))
pattern_5 = generate_pattern((0.15, 20), (0.21, 20), op_one=mul, op_two=mul)

def pattern_4(t: int, iftime: float):
    highest_util = 1.0 - 0.05 * t

    if iftime < 0.99:
        lowest_util = 1.0 - 0.1 * t 
    else:
        lowest_util = 1.0 - 0.3 * t

    return (highest_util, lowest_util)
    
class Patterns:
    _patterns = [pattern_1, pattern_2, pattern_3, pattern_4, pattern_5]

    def __init__(self, random):
        self._random = random
        self._index = 0
        
    def __next__(self):
        if self._random:
            return generate_pattern((random(), random()), (random(), random()))

        return self._patterns[randint(0, len(self._patterns)-1)]
    
