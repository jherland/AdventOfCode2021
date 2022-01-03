from __future__ import annotations

from dataclasses import astuple, dataclass
from heapq import heappop, heappush
from itertools import chain, product
from rich import print
from string import ascii_uppercase
import sys
from typing import Iterable, Iterator

inf = sys.maxsize


@dataclass(frozen=True, order=True)
class Pos:
    y: int
    x: int


class Amphs(dict[Pos, str]):
    def move(self, a: Pos, b: Pos) -> Amphs:
        ret = Amphs(self)
        assert b not in ret
        ret[b] = ret[a]
        del ret[a]
        return ret


Path = list[Pos]
Cost = int


class Burrow:
    @classmethod
    def parse_lines(cls, lines: Iterable[str]) -> tuple[Burrow, Amphs]:
        locations = []
        amphs = Amphs()
        for y, line in enumerate(lines):
            for x, c in enumerate(line.rstrip()):
                pos = Pos(y - 1, x - 1)
                if c in ".ABCD":
                    locations.append(pos)
                    if c != ".":
                        amphs[pos] = c
                else:
                    assert c in " #"
        return cls(locations), amphs
        # TODO: return cls.process_input(locations, amphs)

    @classmethod
    def process_input(cls, locations: list[Pos], amphs: Amphs):
        locations.sort()
        rooms = {p for p in locations if p.y > 0}
        x_columns = {p.x for p in rooms}
        hallways = {p for p in locations if p.y == 0}
        doorways = {p for p in hallways if p.x in x_columns}
        homes = {
            name: {p for p in rooms if p.x == x}
            for name, x in zip(ascii_uppercase, sorted(x_columns))
        }
        costs = {
            name: 10 ** n for n, name in enumerate(sorted(homes.keys()))
        }

        # Pre-calculate all paths:
        def calc_path(start: Path, end: Pos) -> Path | None:
            cur = start[-1]
            assert cur in locations
            y, x = astuple(cur)
            adjacent = [(y - 1, x), (y, x - 1), (y, x + 1), (y + 1, x)]
            for neighbor in [Pos(*p) for p in adjacent if p in locations]:
                if neighbor in start:  # Do not revisit locations
                    continue
                path = start + [neighbor]
                if neighbor == end:
                    return path
                elif (ret := calc_path(path, end)) is not None:
                    return ret
            return None

        paths: dict[Pos, dict[Pos, Path]] = {}  # a -> b -> (a, ..., b]
        # Although an amphipod _could_ move directly from its start position to
        # its home, that path can always be decomposed into two paths (with the
        # same total cost): one into the hallway, followed by another to its
        # home. Thus we only need to consider two types of paths:
        #  - from a room into a hallway (excluding doorways)
        #  - from a hallway (excluding doorways) into a room
        endpoints = chain(
            product(hallways - doorways, rooms),
            product(rooms, hallways - doorways),
        )
        for start, end in endpoints:
            if (path := calc_path([start], end)) is not None:
                assert len(path) >= 2  # "raw" paths include both start and end
                paths.setdefault(start, {})[end] = path[1:]  # skip start

        # TODO:
        # ret = cls(locations, rooms, hallways, )

        # # Pre-calculate what the end result looks like
        # at_home = {p: name for name, homes in homes.items() for p in homes}
        # self.solved = self.state(at_home)
        # assert at_home == self.parse_state(self.solved)  # sanity check



    def __init__(self, locations: Iterable[Pos]):
        self.locations = sorted(locations)
        self.hallways = {p for p in self.locations if p.y == 0}
        self.rooms = {p for p in self.locations if p.y > 0}
        x_columns = {p.x for p in self.rooms}
        self.doorways = {p for p in self.hallways if p.x in x_columns}
        self.homes = {
            name: {p for p in self.rooms if p.x == x}
            for name, x in zip(ascii_uppercase, sorted(x_columns))
        }
        self.costs = {
            name: 10 ** n for n, name in enumerate(sorted(self.homes.keys()))
        }

        # Pre-calculate all paths:
        self.paths: dict[Pos, dict[Pos, Path]] = {}
        # Although an amphipod _could_ move directly from its start position to
        # its home, that path can always be decomposed into two paths (with the
        # same total cost): one into the hallway, followed by another to its
        # home. Thus we only need to consider two types of paths:
        #  - from a room into a hallway (excluding doorways)
        #  - from a hallway (excluding doorways) into a room
        endpoints = chain(
            product(self.hallways - self.doorways, self.rooms),
            product(self.rooms, self.hallways - self.doorways),
        )
        for start, end in endpoints:
            if (path := self._calc_path(end, [start])) is not None:
                assert len(path) >= 2  # "raw" paths include both start and end
                self.paths.setdefault(start, {})[end] = path[1:]  # skip start

        # Pre-calculate what the end result looks like
        at_home = {p: name for name, homes in self.homes.items() for p in homes}
        self.solved = self.state(at_home)
        assert at_home == self.parse_state(self.solved)  # sanity check

    def __str__(self):
        lines = [
            "Burrow:",
            f"  hallways - {len(self.hallways)}: {self.hallways}",
            f"  doorways - {len(self.doorways)}: {self.doorways}",
            f"  rooms - {len(self.rooms)}: {self.rooms}",
            f"  homes - {len(self.homes)}: {self.homes}",
            f"  costs - {len(self.costs)}: {self.costs}",
            f"  paths - {sum(len(d) for d in self.paths.values())}",
            f"  solved - {self.solved!r}",
        ]
        return "\n".join(lines)

    def _calc_path(self, end: Pos, start: Path) -> Path | None:
        pos = start[-1]
        assert pos in self.locations
        y, x = astuple(pos)
        adjacent = [Pos(y - 1, x), Pos(y, x - 1), Pos(y, x + 1), Pos(y + 1, x)]
        for neighbor in [p for p in adjacent if p in self.locations]:
            if neighbor in start:  # Do not revisit locations
                continue
            path = start + [neighbor]
            if neighbor == end:
                return path
            elif (ret := self._calc_path(end, path)) is not None:
                return ret
        return None

    def state(self, amphs: Amphs) -> str:
        return "".join(amphs.get(p, ".") for p in self.locations)

    def parse_state(self, s: str) -> Amphs:
        assert len(s) == len(self.locations)
        # assert all(c in "." + "".join(self.homes.keys()) for c in s)
        return Amphs((pos, c) for c, pos in zip(s, self.locations) if c != ".")

    def available_paths(self, start: Pos, amphs: Amphs) -> Iterator[tuple[Cost, Pos, Pos, Path]]:
        for end, path in self.paths[start].items():  # all possible paths
            if any(pos in amphs for pos in path):
                continue  # discard paths that collide with other amphipods
            # If the path ends in a room, it _must_ be the lowest available
            # location in the home room, and it cannot block any foreigners.
            a = amphs[start]
            if end in self.rooms:
                if end not in self.homes[a]:
                    continue  # discard paths that end in foreign rooms
                below = {pos for pos in self.homes[a] if pos.y > end.y}
                if not all(amphs.get(pos) == a for pos in below):
                    continue  # only move home when it will not block others
            yield (self.costs[a] * len(path)), start, end, path

    def all_available_paths(self, amphs: Amphs) -> Iterator[tuple[Cost, Pos, Pos, Path]]:
        for pos in amphs.keys():
            yield from self.available_paths(pos, amphs)


def solve(lines: Iterable[str]) -> Cost:
    burrow, amphs = Burrow.parse_lines(lines)
    print(str(burrow))

    def next_state(state: str) -> Iterator[tuple[Cost, str]]:
        amphs = burrow.parse_state(state)
        for cost, start, end, path in burrow.all_available_paths(amphs):
            yield cost, burrow.state(amphs.move(start, end))

    queue = [(0, burrow.state(amphs))]
    seen = {burrow.state(amphs): 0}
    while queue:
        cost, current = heappop(queue)
        # print(f"Queue is {len(queue):6} long, considering {cost:5} / {current}")
        if current == burrow.solved:
            return cost
        for dcost, next in next_state(current):
            new_cost = cost + dcost
            if new_cost < seen.get(next, inf):
                seen[next] = new_cost
                heappush(queue, (new_cost, next))
                # print(f"  Added {new_cost:5} / {next}")


with open("23.input") as f:
    lines = f.readlines()

# lines = """\
# #############
# #.A.........#
# ###.#B#C#D###
#   #A#B#C#D#
#   #########
# """.split("\n")

# Part 1:
print(solve(lines))

# Part 2:
# lines = lines[:3] + ["  #D#C#B#A#", "  #D#B#A#C#"] + lines[3:]
# print(solve(lines))


# Part 1:
# 18051 is correct!

# Part 2:
# 50245 is correct!
