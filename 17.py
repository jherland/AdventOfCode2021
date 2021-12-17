from __future__ import annotations

from dataclasses import dataclass
from itertools import takewhile
from rich import print
from typing import Iterator


@dataclass
class Pos:
    x: int
    y: int


@dataclass
class Area:
    bottom_left: Pos
    top_right: Pos

    def __post_init__(self):
        assert self.bottom_left.x < self.top_right.x
        assert self.bottom_left.y < self.top_right.y

    def __contains__(self, pos: Pos) -> bool:
        return (
            self.bottom_left.x <= pos.x <= self.top_right.x
            and self.bottom_left.y <= pos.y <= self.top_right.y
        )

    def out_of_bounds(self, pos: Pos) -> bool:
        return pos.x > self.top_right.x or pos.y < self.bottom_left.y


@dataclass(frozen=True)
class Probe:
    pos: Pos
    vel: Pos

    def next(self) -> Probe:
        pos = Pos(self.pos.x + self.vel.x, self.pos.y + self.vel.y)
        dx = -1 if self.vel.x > 0 else (+1 if self.vel.x < 0 else 0)
        vel = Pos(self.vel.x + dx, self.vel.y - 1)
        return self.__class__(pos, vel)

    def trace(self) -> Iterator[Pos]:
        while True:
            yield self.pos
            self = self.next()


def find_trajectories(target_area: Area) -> Iterator[tuple[Probe, list[Pos]]]:
    for vx in range(target_area.top_right.x + 1):
        max_x_pos = vx * (vx + 1) / 2  # triangular number
        if max_x_pos < target_area.bottom_left.x:
            continue  # will never reach target area
        for vy in range(100, target_area.bottom_left.y - 1, -1):
            probe = Probe(Pos(0, 0), Pos(vx, vy))
            ps = list(
                takewhile(
                    lambda pos: not target_area.out_of_bounds(pos),
                    probe.trace(),
                )
            )
            if ps[-1] in target_area:
                yield probe, ps


with open("17.input") as f:
    line = f.read().rstrip()
    prefix, xstr, ystr = line.split("=")
    assert prefix == "target area: x"
    assert xstr.endswith(", y")
    x1, _, x2 = xstr[:-3].split(".")
    y1, _, y2 = ystr.split(".")
    target_area = Area(Pos(int(x1), int(y1)), Pos(int(x2), int(y2)))

trajectories = list(find_trajectories(target_area))

# Part 1: Highest y position reached by any successful trajectory?
print(max(max(p.y for p in ps) for _, ps in trajectories))

# Part 2: How many successful trajectories?
print(len(trajectories))
