from __future__ import annotations
from contextlib import suppress
from dataclasses import dataclass, field
from math import prod
from typing import Iterable, Iterator

Position = tuple[int, int]


@dataclass
class HeightMap:
    d: dict[Position, int] = field(default_factory=dict)
    height: int = 0
    width: int = 0

    @classmethod
    def parse(cls, lines: Iterable[str]) -> HeightMap:
        ret = cls()
        for y, line in enumerate(lines):
            for x, char in enumerate(line.rstrip()):
                ret[(y, x)] = int(char)
        return ret

    def __str__(self) -> str:
        lines = [f"<{self.height}x{self.width}>:"]
        for y in range(self.height):
            line = []
            for x in range(self.width):
                line.append(self.d.get((y, x), " "))
            lines.append("".join(map(str, line)))
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.d)

    def __contains__(self, pos: Position) -> bool:
        return pos in self.d

    def __getitem__(self, pos: Position) -> int:
        return self.d[pos]

    def __setitem__(self, pos: Position, value: int) -> None:
        y, x = pos
        self.height = max(self.height, y + 1)
        self.width = max(self.width, x + 1)
        self.d[(y, x)] = value

    def __iter__(self) -> Iterator[tuple[Position, int]]:
        for y in range(self.height):
            for x in range(self.width):
                with suppress(KeyError):
                    yield (y, x), self.d[(y, x)]

    def neighbors(self, pos: Position) -> Iterator[tuple[Position, int]]:
        y, x = pos
        for npos in {(y - 1, x), (y, x - 1), (y + 1, x), (y, x + 1)}:
            with suppress(KeyError):
                yield npos, self.d[npos]


def find_low_points(hmap: HeightMap) -> Iterator[tuple[Position, int]]:
    for pos, h in hmap:
        if all(nh > h for _, nh in hmap.neighbors(pos)):
            yield pos, h


def find_basins(hmap: HeightMap) -> Iterator[HeightMap]:
    processed = set()  # all (y, x) that have been processed

    def grow_basin(pos):
        ret = HeightMap()
        nbors = {pos}
        while nbors:
            pos = nbors.pop()
            assert pos not in processed
            ret[pos] = hmap[pos]
            processed.add(pos)
            for npos, nh in hmap.neighbors(pos):
                if nh == 9 or npos in processed:
                    continue
                nbors.add(npos)
        return ret

    for pos, h in hmap:
        if h == 9 or pos in processed:  # skip tops and already-processed
            continue
        yield grow_basin(pos)  # pos belongs to a new basin


with open("09.input") as f:
    hmap = HeightMap.parse(f)

# Part 1: What is the sum of the risk levels of all low points in the map?
print(sum(h + 1 for _, h in find_low_points(hmap)))

# Part 2: What is the product of the sizes of the three largest basins?
print(prod(sorted([len(basin) for basin in find_basins(hmap)])[-3:]))
