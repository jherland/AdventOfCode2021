from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import chain, product
from rich import print
from string import ascii_uppercase
import sys
from typing import Iterable, Iterator, NamedTuple

inf = sys.maxsize


class Pos(NamedTuple):
    y: int
    x: int


Index = int
Cost = int
State = str


@dataclass
class Burrow:
    length: Index
    room_index: Index  # all indices >= this are rooms
    homes: dict[str, set[Index]]
    costs: dict[str, int]
    paths: list[list[list[Index]]]  # start -> end -> (start, ... , end]
    solved: State

    @classmethod
    def parse_lines(cls, lines: Iterable[str]) -> tuple[Burrow, State]:
        locations = []
        amphs = {}
        for y, line in enumerate(lines):
            for x, c in enumerate(line.rstrip()):
                pos = Pos(y - 1, x - 1)
                if c in ".ABCD":
                    locations.append(pos)
                    if c != ".":
                        amphs[pos] = c
                else:
                    assert c in " #"
        return cls.preprocess(locations, amphs)

    @classmethod
    def preprocess(cls, locations: list[Pos], amphs: dict[Pos, str]) -> tuple[Burrow, State]:
        locations.sort()
        rooms = {p for p in locations if p.y > 0}
        x_columns = {p.x for p in rooms}
        hallways = {p for p in locations if p.y == 0}
        doorways = {p for p in hallways if p.x in x_columns}
        homes = {
            name: {p for p in rooms if p.x == x}
            for name, x in zip(ascii_uppercase, sorted(x_columns))
        }
        costs = {name: 10 ** n for n, name in enumerate(sorted(homes.keys()))}

        # Pre-calculate all paths:
        def calc_path(start: list[Pos], end: Pos) -> list[Pos] | None:
            cur = start[-1]
            assert cur in locations
            y, x = cur
            adj = [Pos(y - 1, x), Pos(y, x - 1), Pos(y, x + 1), Pos(y + 1, x)]
            for neighbor in [pos for pos in adj if pos in locations]:
                if neighbor in start:  # Do not revisit locations
                    continue
                path = start + [neighbor]
                if neighbor == end:
                    return path
                elif (ret := calc_path(path, end)) is not None:
                    return ret
            return None

        paths: dict[Pos, dict[Pos, list[Pos]]] = {}  # a -> b -> (a, ..., b]
        # Although an amphipod _could_ move directly from its start position to
        # its home, that path can always be decomposed into two paths (with the
        # same total cost): one into the hallway, followed by another to its
        # home. Thus we only need to consider two types of paths:
        #  - from a room into a hallway (excluding doorways)
        #  - from a hallway (excluding doorways) into a room
        endpoints = list(chain(
            product(hallways - doorways, rooms),
            product(rooms, hallways - doorways),
        ))
        for start, end in endpoints:
            if (path := calc_path([start], end)) is not None:
                assert len(path) >= 2  # "raw" paths include both start and end
                paths.setdefault(start, {})[end] = path[1:]  # skip start

        if True:
            print("Burrow:")
            print(f"  hallways - {len(hallways)}: {hallways}")
            print(f"  doorways - {len(doorways)}: {doorways}")
            print(f"  rooms - {len(rooms)}: {rooms}")
            print(f"  homes - {len(homes)}: {homes}")
            print(f"  costs - {len(costs)}: {costs}")
            print(f"  paths - {sum(len(d) for d in paths.values())}")

        # Now convert all 2D Pos coordinates to 1D indices into state strings
        pos_to_i = locations.index

        def set_pos_to_i(s: set[Pos]) -> set[Index]:
            return {pos_to_i(pos) for pos in s}

        def build_state(amphs: dict[Pos, str]) -> State:
            return "".join(amphs.get(pos, ".") for pos in locations)

        ret = cls(
            len(locations),
            min(set_pos_to_i(rooms)),
            {k: set_pos_to_i(v) for k, v in homes.items()},
            costs,
            [
                [
                    ([pos_to_i(p) for p in paths[start][end]] if start in paths and end in paths[start] else None) for end in locations
                ] for start in locations
            ],
            build_state({p: name for name, ps in homes.items() for p in ps})
        )
        print(ret)
        return ret, build_state(amphs)

    def available_paths(self, state: str, i: Index) -> Iterator[tuple[Cost, Index, Index]]:
        a = state[i]
        assert a != '.'
        for j, path in enumerate(self.paths[i]):  # all possible paths from i
            if path is None:
                continue  # no path
            if any(state[k] != '.' for k in path):
                continue  # discard paths that collide with other amphipods
            # If the path ends in a room, it _must_ be the deepest available
            # location in that home room, and it cannot block any foreigners.
            if j >= self.room_index:
                if j not in self.homes[a]:
                    continue  # discard paths that end in foreign rooms
                if not all(state[k] == a for k in self.homes[a] if k > j):
                    continue  # only move home when it will not block others
            yield (self.costs[a] * len(path)), i, j

    def all_available_paths(self, state: str) -> Iterator[tuple[Cost, Index, Index]]:
        for i, c in enumerate(state):
            if c != '.':
                yield from self.available_paths(state, i)

    def move(self, state: State, a: Index, b: Index) -> State:
        assert state[a] in self.homes
        assert state[b] == '.'
        return "".join(
            {a: state[b], b: state[a]}.get(i, c)
            for i, c in enumerate(state)
        )


def solve(lines: Iterable[str]) -> Cost:
    burrow, state = Burrow.parse_lines(lines)

    def next_state(state: State) -> Iterator[tuple[Cost, State]]:
        for cost, start, end in burrow.all_available_paths(state):
            yield cost, burrow.move(state, start, end)

    queue = [(0, state)]
    seen = {state: 0}
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
