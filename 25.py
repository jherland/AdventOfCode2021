from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import count
from rich import print
from typing import Iterable, Iterator


@dataclass(frozen=True, slots=True)
class Pos:
    y: int
    x: int


@dataclass(frozen=True, eq=True, slots=True)
class Map:
    east: set[Pos]
    south: set[Pos]
    size: Pos

    @classmethod
    def parse(cls, lines: Iterable[str]) -> Map:
        east, south = set(), set()
        for y, line in enumerate(lines):
            for x, c in enumerate(line.rstrip()):
                pos = Pos(y, x)
                if c == ">":
                    east.add(pos)
                elif c == "v":
                    south.add(pos)
                else:
                    assert c == "."  # empty
        size = Pos(y + 1, x + 1)
        assert all(p.y < size.y and p.x < size.x for p in east | south)
        return cls(east, south, size)

    def __str__(self) -> str:
        return "\n".join(
            "".join(
                {
                    (True, False): ">",
                    (False, True): "v",
                    (False, False): ".",
                }[(Pos(y, x) in self.east, Pos(y, x) in self.south)]
                for x in range(self.size.x)
            )
            for y in range(self.size.y)
        )

    def __contains__(self, pos: Pos) -> bool:
        return pos in self.east or pos in self.south

    def next(self) -> Map:
        def next_east(east: Iterable[Pos]) -> Iterator[Pos]:
            width = self.size.x
            for pos in east:
                npos = Pos(pos.y, (pos.x + 1) % width)
                yield pos if npos in self else npos

        def next_south(south: Iterable[Pos]) -> Iterator[Pos]:
            height = self.size.y
            for pos in south:
                npos = Pos((pos.y + 1) % height, pos.x)
                yield pos if npos in self else npos

        self = replace(self, east=set(next_east(self.east)))
        return replace(self, south=set(next_south(self.south)))

    def move_until_blockade(self) -> tuple[Map, int]:
        for step in count(1):
            next = self.next()
            if self == next:
                return self, step
            self = next


with open("25.input") as f:
    seafloor = Map.parse(f)

# Part 1: How many steps until no sea cucumber can move
print(seafloor.move_until_blockade()[1])


# Unit tests


def test_simple_east_movement():
    m = Map.parse(["...>>>>>..."])
    m = m.next()
    assert str(m) == "...>>>>.>..", str(m)
    m = m.next()
    assert str(m) == "...>>>.>.>.", str(m)


def test_east_moves_before_south():
    m = Map.parse(
        [
            "..........",
            ".>v....v..",
            ".......>..",
            "..........",
        ]
    )
    m = m.next()
    assert str(m).split("\n") == [
        "..........",
        ".>........",
        "..v....v>.",
        "..........",
    ]


def test_wraparound():
    m = Map.parse(
        [
            "...>...",
            ".......",
            "......>",
            "v.....>",
            "......>",
            ".......",
            "..vvv..",
        ]
    )
    m = m.next()
    assert str(m).split("\n") == [
        "..vv>..",
        ".......",
        ">......",
        "v.....>",
        ">......",
        ".......",
        "....v..",
    ]
    m = m.next()
    assert str(m).split("\n") == [
        "....v>.",
        "..vv...",
        ".>.....",
        "......>",
        "v>.....",
        ".......",
        ".......",
    ]
    m = m.next()
    assert str(m).split("\n") == [
        "......>",
        "..v.v..",
        "..>v...",
        ">......",
        "..>....",
        "v......",
        ".......",
    ]
    m = m.next()
    assert str(m).split("\n") == [
        ">......",
        "..v....",
        "..>.v..",
        ".>.v...",
        "...>...",
        ".......",
        "v......",
    ]


def test_example_stops_after_58_steps():
    with open("25.example.input") as f:
        m = Map.parse(f)
    m, steps = m.move_until_blockade()
    assert steps == 58
    state = str(m)
    assert state.split("\n") == [
        "..>>v>vv..",
        "..v.>>vv..",
        "..>>v>>vv.",
        "..>>>>>vv.",
        "v......>vv",
        "v>v....>>v",
        "vvv.....>>",
        ">vv......>",
        ".>v.vv.v..",
    ]
    m = m.next()
    assert str(m) == state  # unchanged


def test():
    test_simple_east_movement()
    test_east_moves_before_south()
    test_wraparound()
    test_example_stops_after_58_steps()


test()
