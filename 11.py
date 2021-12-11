from contextlib import suppress
from rich import print


def parse_levels(lines):
    for y, line in enumerate(lines):
        for x, char in enumerate(line.rstrip()):
            yield (y, x), int(char)


def adjacent(pos):
    y, x = pos
    return [
        (y - 1, x - 1), (y - 1, x), (y - 1, x + 1),
        (y, x - 1), (y, x + 1),
        (y + 1, x - 1), (y + 1, x), (y + 1, x + 1),
    ]


def next_turn(levels):
    ret = {pos: level + 1 for pos, level in levels.items()}
    flash = {pos for pos, level in ret.items() if level > 9}
    flashed = set()
    while flash - flashed:
        for pos in flash - flashed:
            for npos in adjacent(pos):
                with suppress(KeyError):
                    ret[npos] += 1
                    if ret[npos] > 9:
                        flash.add(npos)
            flashed.add(pos)
    assert flash == flashed
    for pos in flashed:
        ret[pos] = 0
    return ret, len(flashed)


def lprint(levels):
    for y in range(10):
        for x in range(10):
            print(levels[(y, x)], end="")
        print()


with open("11.input") as f:
    levels = {pos: level for pos, level in parse_levels(f)}

# Part 1: How many flashes in the first 100 steps
flashes, gen = 0, 0
for _ in range(100):
    levels, flashed = next_turn(levels)
    flashes += flashed
    gen += 1
print(flashes)

# Part 2: How many steps until all octopuses flash
while flashed < len(levels):
    levels, flashed = next_turn(levels)
    gen += 1
print(gen)

