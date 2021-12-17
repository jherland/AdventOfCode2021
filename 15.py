from __future__ import annotations

from collections import defaultdict
from contextlib import suppress
from itertools import chain
from rich import print
import sys
from typing import Iterable, Iterator

Position = tuple[int, int]
inf = sys.maxsize


class Map(dict[Position, int]):
    def __init__(self, iterable: Iterable[tuple[Position, int]] = ()):
        super().__init__()
        self.height = 0
        self.width = 0
        for pos, val in iterable if iterable is not None else []:
            self[pos] = val

    def __setitem__(self, pos: Position, value: int) -> None:
        super().__setitem__(pos, value)
        y, x = pos
        self.height = max(self.height, y + 1)
        self.width = max(self.width, x + 1)

    def render(self):
        ret = []
        for y in range(self.height):
            for x in range(self.width):
                ret.append(str(self[(y, x)]))
            ret.append("\n")
        return "".join(ret)

    def adjacent(self, pos: Position) -> Iterator[tuple[Position, int]]:
        y, x = pos
        for npos in [(y, x + 1), (y + 1, x), (y, x - 1), (y - 1, x)]:
            with suppress(KeyError):
                yield npos, self[npos]

    def multiply(self, my: int, mx: int) -> Map:
        def repeated(ny: int, nx: int) -> Iterator[tuple[Position, int]]:
            """Copy of 'self' with offsets applied and values updated."""
            dy = self.height * ny
            dx = self.width * nx
            return (
                ((y + dy, x + dx), (val + ny + nx - 1) % 9 + 1)
                for (y, x), val in self.items()
            )

        ret = Map(
            chain.from_iterable(
                repeated(ny, nx) for ny in range(my) for nx in range(mx)
            )
        )
        ret.height = my * self.height
        ret.width = my * self.width
        return ret


def manhattan_dist(a: Position, b: Position) -> int:
    ay, ax = a
    by, bx = b
    return abs(bx - ax) + abs(by - ay)


def find_min_path(map: Map, start: Position, end: Position) -> int:
    # A* algorithm
    def guess(pos: Position) -> int:
        return 2 * manhattan_dist(pos, end)

    open_set = {start}
    distance: dict[Position, int] = defaultdict(lambda: inf)
    distance[start] = 0
    best_guess: dict[Position, int] = defaultdict(lambda: inf)
    best_guess[start] = guess(start)
    while open_set:
        current = min(open_set, key=lambda pos: best_guess[pos])
        if current == end:
            break  # found shortest path to end node
        open_set.remove(current)
        for nbor, dist in map.adjacent(current):
            tentative = distance[current] + dist
            if tentative < distance[nbor]:  # found better path to neighbor
                distance[nbor] = tentative
                best_guess[nbor] = tentative + guess(nbor)
                open_set.add(nbor)
    return distance[end]


with open("15.input") as f:
    cavern = Map(
        ((y, x), int(c))
        for y, line in enumerate(f)
        for x, c in enumerate(line.rstrip())
    )

# Part 1: Find minimum path from top left to bottom right
print(find_min_path(cavern, (0, 0), (cavern.height - 1, cavern.width - 1)))

# Part 2: Find minimum path in 5x5 cavern from top left to bottom right
cavern = cavern.multiply(5, 5)
print(find_min_path(cavern, (0, 0), (cavern.height - 1, cavern.width - 1)))
