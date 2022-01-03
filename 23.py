from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import chain, product
from rich import print
from string import ascii_uppercase
import sys
from typing import Iterable, Iterator, NamedTuple

DEBUG = False
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
    paths: list[list[list[Index] | None]]  # start -> end -> (start, ... , end]
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
    def preprocess(
        cls, locations: list[Pos], amphs: dict[Pos, str]
    ) -> tuple[Burrow, State]:
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
        endpoints = chain(
            product(hallways - doorways, rooms),
            product(rooms, hallways - doorways),
        )
        for start, end in endpoints:
            if (path := calc_path([start], end)) is not None:
                assert len(path) >= 2  # "raw" paths include both start and end
                paths.setdefault(start, {})[end] = path[1:]  # skip start

        if DEBUG:
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

        def to_state(amphs: dict[Pos, str]) -> State:
            return "".join(amphs.get(pos, ".") for pos in locations)

        ret = cls(
            len(locations),
            min(set_pos_to_i(rooms)),
            {k: set_pos_to_i(v) for k, v in homes.items()},
            costs,
            [
                [
                    (
                        [pos_to_i(p) for p in paths[start][end]]
                        if start in paths and end in paths[start]
                        else None
                    )
                    for end in locations
                ]
                for start in locations
            ],
            to_state({p: name for name, ps in homes.items() for p in ps}),
        )
        return ret, to_state(amphs)

    def available_paths(
        self, state: str, i: Index
    ) -> Iterator[tuple[Cost, Index, Index]]:
        a = state[i]
        assert a != "."

        def interesting_paths() -> Iterator[list[Index]]:
            if i >= self.room_index:  # outbound travel, search prebuilt paths
                yield from (path for path in self.paths[i] if path is not None)
            else:  # inbound travel, only one potential path
                # There is only one possible destination: the deepest available
                # location in this amphipod's home room, and it can only be used
                # if no foreigners end up blocked below.
                for j in sorted(self.homes[a], reverse=True):
                    if state[j] == ".":  # first available location
                        path = self.paths[i][j]
                        assert path is not None
                        yield path
                        break  # done
                    elif state[j] != a:  # foreign amphipod
                        break  # cannot move home yet

        for path in interesting_paths():
            if not any(state[k] != "." for k in path):  # no collision
                yield (self.costs[a] * len(path)), i, path[-1]

    def all_available_paths(
        self, state: str
    ) -> Iterator[tuple[Cost, Index, Index]]:
        for i, c in enumerate(state):
            if c != ".":
                yield from self.available_paths(state, i)

    def move(self, state: State, a: Index, b: Index) -> State:
        assert state[a] in self.homes
        assert state[b] == "."
        return "".join(
            {a: state[b], b: state[a]}.get(i, c) for i, c in enumerate(state)
        )


def solve(lines: Iterable[str]) -> Cost:
    burrow, state = Burrow.parse_lines(lines)
    queue = [(0, state)]
    seen = {state: 0}
    while queue:
        cost, state = heappop(queue)
        if DEBUG:
            print(f"Queue is {len(queue):6}, looking at {state} @ {cost}")
        if state == burrow.solved:
            return cost

        for dcost, start, end in burrow.all_available_paths(state):
            new_state = burrow.move(state, start, end)
            new_cost = cost + dcost
            if new_cost < seen.get(new_state, inf):
                seen[new_state] = new_cost
                heappush(queue, (new_cost, new_state))
    raise RuntimeError("No solution!")


with open("23.input") as f:
    lines = f.readlines()

# Part 1: What is the least energy required to organize the amphipods?
print(solve(lines))  # 18051

# Part 2: Repeat part 1, but with unfolded burrows
lines = lines[:3] + ["  #D#C#B#A#", "  #D#B#A#C#"] + lines[3:]
print(solve(lines))  # 50245
