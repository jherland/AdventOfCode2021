from __future__ import annotations

from collections import defaultdict
from rich import print
from typing import Iterator, NamedTuple


class Pos(NamedTuple):
    y: int
    x: int


class Image:
    @classmethod
    def parse(cls, lines: Iterator[str]) -> Image:
        ret = cls()
        for y, line in enumerate(lines):
            for x, c in enumerate(line.rstrip()):
                ret[Pos(y, x)] = c == "#"
        return ret

    def __init__(self, default: bool = False):
        self.pixels: dict[Pos, bool] = defaultdict(lambda: default)
        self.default = default
        self.y_min = self.y_max = self.x_min = self.x_max = 0

    def __len__(self):
        assert self.default is False  # otherwise our answer is infinite
        return sum(self.pixels.values())

    def __str__(self):
        lines = []
        for y in range(self.y_min - 1, self.y_max + 2):
            line = []
            for x in range(self.x_min - 1, self.x_max + 2):
                line.append("#" if self[Pos(y, x)] else ".")
            lines.append("".join(line))
        return "\n".join(lines)

    def __getitem__(self, pos: Pos) -> bool:
        return self.pixels[pos]

    def __setitem__(self, pos: Pos, val: bool) -> None:
        y, x = pos
        self.pixels[pos] = val
        self.y_min = min(self.y_min, y)
        self.y_max = max(self.y_max, y)
        self.x_min = min(self.x_min, x)
        self.x_max = max(self.x_max, x)

    @staticmethod
    def adjacent(pos: Pos) -> list[Pos]:
        Y, X = pos
        return [Pos(y, x) for y in [Y - 1, Y, Y + 1] for x in [X - 1, X, X + 1]]

    def code(self, pos: Pos) -> int:
        v = int("".join("1" if self[p] else "0" for p in self.adjacent(pos)), 2)
        assert 0 <= v < 512
        return v

    def enhance(self, algo: list[bool]) -> Image:
        assert len(algo) == 512
        ret = self.__class__(default=algo[0b111111111 if self.default else 0])
        # Output image "grows" by 1 pixel in all 4 directions
        for y in range(self.y_min - 1, self.y_max + 2):
            for x in range(self.y_min - 1, self.y_max + 2):
                ret[Pos(y, x)] = algo[self.code(Pos(y, x))]
        return ret

    def enhance_n(self, algo: list[bool], n: int) -> Image:
        img = self
        for _ in range(n):
            img = img.enhance(algo)
        return img


with open("20.input") as f:
    algo = [c == "#" for c in f.readline().rstrip()]
    assert len(algo) == 512
    assert f.readline().rstrip() == ""
    img = Image.parse(f)

# Part 1: How many pixels are lit after 2 enhancements
print(len(img.enhance_n(algo, 2)))

# Part 2: How many pixels are lit after 50 enhancements
print(len(img.enhance_n(algo, 50)))
