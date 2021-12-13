from functools import partial
from typing import Callable, Iterator

Bits = tuple[int, ...]
Candidates = list[Bits]
BitFilter = Callable[[Bits], bool]


def parse_line(line: str) -> Bits:
    return tuple(int(bit) for bit in line.strip())


def most_common_bit(candidates: Candidates, pos: int) -> int:
    # return 1 if number of 1s and 0s are exactly equal.
    return int(sum(c[pos] for c in candidates) * 2 >= len(candidates))


def common_bit_filter(
    pos: int, candidates: Candidates, least: bool = False
) -> BitFilter:
    common_bit = most_common_bit(candidates, pos)
    if least:
        common_bit = 1 - common_bit
    return lambda c: c[pos] == common_bit


def progressively_filter(
    candidates: Candidates,
    filter_factories: Iterator[Callable[[Candidates], BitFilter]],
) -> Bits:
    while len(candidates) > 1:
        filter = next(filter_factories)(candidates)
        candidates = [c for c in candidates if filter(c)]
    return candidates[0]


def as_int(bits: Bits) -> int:
    return int("".join(map(str, bits)), 2)


with open("03.input") as f:
    rows = [parse_line(line) for line in f]
    nbits = len(rows[0])

# Part 1: Power consumption = gamma rate * epsilon rate
gamma = tuple(most_common_bit(rows, i) for i in range(nbits))
epsilon = tuple(1 - g for g in gamma)
print(as_int(gamma) * as_int(epsilon))

# Part 2: Life support rating = oxygen generator rating * CO2 scrubber rating
ogr_filters = (partial(common_bit_filter, i) for i in range(nbits))
ogr = progressively_filter(list(rows), ogr_filters)
csr_filters = (partial(common_bit_filter, i, least=True) for i in range(nbits))
csr = progressively_filter(list(rows), csr_filters)
print(as_int(ogr) * as_int(csr))
