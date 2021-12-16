from contextlib import suppress
from itertools import chain
import sys
from typing import Dict, Iterable, Iterator, Tuple

Position = Tuple[int, int]
inf = sys.maxsize


class Map(Dict[Position, int]):
    def __init__(self, iterable: Iterable[Tuple[Position, int]] = ()):
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

    def adjacent(self, pos: Position) -> Iterator[Tuple[Position, int]]:
        y, x = pos
        for npos in [(y, x + 1), (y + 1, x), (y, x - 1), (y - 1, x)]:
            with suppress(KeyError):
                yield npos, self[npos]

    def multiply(self, my: int, mx: int) -> "Map":
        def repeated(ny: int, nx: int) -> Iterator[Tuple[Position, int]]:
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


def find_min_path(map: Map, start: Position, end: Position) -> int:
    # Dijkstra's algorithm
    distance: Dict[Position, int] = dict.fromkeys(map.keys(), inf)
    distance[start] = 0
    unvisited = set(distance.keys())
    current = start
    while True:
        for nbor, dist in map.adjacent(current):
            if nbor in unvisited:
                distance[nbor] = min(distance[nbor], distance[current] + dist)
        unvisited.remove(current)
        if current == end:
            break  # found shortest path to end node
        current = min(unvisited, key=lambda pos: distance[pos])
        if distance[current] == inf:
            break  # disconnected from remaining nodes
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
