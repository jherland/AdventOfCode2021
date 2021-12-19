from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from itertools import combinations
from rich import print
from typing import Iterator


@dataclass(frozen=True)
class Pos:
    x: int
    y: int
    z: int

    @classmethod
    def parse(cls, line: str) -> Pos:
        return cls(*[int(s) for s in line.rstrip().split(",")])

    def __str__(self) -> str:
        return f"({self.x},{self.y},{self.z})"

    def __add__(self, pos: object) -> Pos:
        if not isinstance(pos, Pos):
            return NotImplemented
        return self.__class__(self.x + pos.x, self.y + pos.y, self.z + pos.z)

    def vdist(self, pos: Pos) -> Pos:
        return self.__class__(pos.x - self.x, pos.y - self.y, pos.z - self.z)

    def mhdist(self, pos: Pos) -> int:
        vd = self.vdist(pos)
        return abs(vd.x) + abs(vd.y) + abs(vd.z)


Rotation = [
    # Keep Z constant, and rotate XY plane
    lambda pos: Pos(pos.x, pos.y, pos.z),
    lambda pos: Pos(-pos.y, pos.x, pos.z),
    lambda pos: Pos(-pos.x, -pos.y, pos.z),
    lambda pos: Pos(pos.y, -pos.x, pos.z),
    # Flip Z, rotate XY plane
    lambda pos: Pos(pos.y, pos.x, -pos.z),
    lambda pos: Pos(-pos.x, pos.y, -pos.z),
    lambda pos: Pos(-pos.y, -pos.x, -pos.z),
    lambda pos: Pos(pos.x, -pos.y, -pos.z),
    # Move +Z to +X, rotate XY plane
    lambda pos: Pos(pos.z, pos.x, pos.y),
    lambda pos: Pos(pos.z, pos.y, -pos.x),
    lambda pos: Pos(pos.z, -pos.x, -pos.y),
    lambda pos: Pos(pos.z, -pos.y, pos.x),
    # Move +Z to -X, rotate XY plane
    lambda pos: Pos(-pos.z, pos.y, pos.x),
    lambda pos: Pos(-pos.z, pos.x, -pos.y),
    lambda pos: Pos(-pos.z, -pos.y, -pos.x),
    lambda pos: Pos(-pos.z, -pos.x, pos.y),
    # Move +Z to +Y, rotate XY plane
    lambda pos: Pos(pos.y, pos.z, pos.x),
    lambda pos: Pos(-pos.x, pos.z, pos.y),
    lambda pos: Pos(-pos.y, pos.z, -pos.x),
    lambda pos: Pos(pos.x, pos.z, -pos.y),
    # Move +Z to -Y, rotate XY plane
    lambda pos: Pos(pos.x, -pos.z, pos.y),
    lambda pos: Pos(-pos.y, -pos.z, pos.x),
    lambda pos: Pos(-pos.x, -pos.z, -pos.y),
    lambda pos: Pos(pos.y, -pos.z, -pos.x),
]
assert len({rot(Pos(1, 2, 3)) for rot in Rotation}) == len(Rotation)

XForm = tuple[Pos, int]  # Encode a transformation as a translation + a rotation


def transform(xform: XForm, pos: Pos) -> Pos:
    translate, rotate = xform
    return Rotation[rotate](pos) + translate


@dataclass
class Scanner:
    id: str
    beacons: set[Pos]
    int_dists: dict[Pos, dict[Pos, int]] = field(default_factory=dict)
    pos: Pos = Pos(0, 0, 0)

    @classmethod
    def parse(cls, lines: Iterator[str], id: str) -> Scanner:
        beacons = set()
        for line in lines:
            if not line.rstrip():
                break  # end parsing at blank line
            beacons.add(Pos.parse(line))
        return cls(id, beacons)

    def __post_init__(self):
        if not self.int_dists:
            for b in self.beacons:
                self.int_dists[b] = {c: b.mhdist(c) for c in self.beacons - {b}}

    def __str__(self) -> str:
        return f"<scanner {self.id}>"

    def internal_dists(self, pos: Pos) -> tuple[set[int], int]:
        assert pos in self.beacons
        ret = set(self.int_dists[pos].values())
        equidists = len(self.int_dists[pos]) - len(ret)
        return ret, equidists

    def correlated_beacons(self, other: Scanner) -> Iterator[tuple[Pos, Pos]]:
        """Find corresponding beacons between this and the given scanner.

        Use equal internal distances to find candidates for common (pairs of)
        beacons between two scanners. We need at least 12 common beacons to
        establish a correlation between two scanners. However, sometimes the
        internal distances from one beacon to all other are not unique...
        """
        for sb in self.beacons:
            for ob in other.beacons:
                sb_dists, sb_eqd = self.internal_dists(sb)
                ob_dists, ob_eqd = other.internal_dists(ob)
                # We need sb and ob to each agree on the distance to _11_ other
                # beacons from their respective scanners, in order to establish
                # a correlation. However, there are some equidistant beacons
                # that are collapsed in the sets of distances. We relax our
                # requirement down from 11 matching distances, accordingly.
                # Note that this will break down when there are _many_ equi-
                # distant beacons.
                required_overlap = 11 - max(sb_eqd, ob_eqd)
                overlap = sb_dists & ob_dists
                if len(overlap) >= required_overlap:
                    yield sb, ob

    def orient(self, other: Scanner, overlap: set[tuple[Pos, Pos]]) -> XForm:
        """Orient a scanner relative to self, based on correlated beacons.

        Return a transform function that converts a position relative to the
        given scanner to the corresponding position relative to this scanner.
        """
        assert len(overlap) == 12
        spos, opos = next(iter(overlap))
        assert spos in self.beacons and opos in other.beacons
        for rot, rot_func in enumerate(Rotation):
            translate = rot_func(opos).vdist(spos)
            xform = (translate, rot)
            assert transform(xform, opos) == spos
            # Does this candidate correctly transform all corresponding points?
            if all(spos == transform(xform, opos) for spos, opos in overlap):
                return xform
        raise ValueError(f"Failed to orient {other} relative to {self}")

    def reorient(self, other: Scanner) -> Scanner | None:
        overlap = set(self.correlated_beacons(other))
        if not overlap:
            return None
        xform = self.orient(other, overlap)
        return self.__class__(
            f"{other.id}@{xform}/{self.id}",
            {transform(xform, pos) for pos in other.beacons},
            {
                transform(xform, pos): {
                    transform(xform, p): d
                    for p, d in other.int_dists[pos].items()
                }
                for pos in other.beacons
            },
            transform(xform, other.pos),
        )


scanners: list[Scanner] = []
with open("19.input") as f:
    for line in f:
        assert line.startswith("--- scanner ") and line.endswith(" ---\n")
        scanners.append(Scanner.parse(f, line[12:-5]))

# Reorient all scanners in terms of their direct connections
scanner_graph: dict[int, dict[int, Scanner]] = {}
for i, scanner_i in enumerate(scanners):
    scanner_graph.setdefault(i, {})
    for j, scanner_j in enumerate(scanners):
        if i == j:
            scanner_graph[i][j] = scanner_i
        else:
            new_j = scanner_i.reorient(scanner_j)
            if new_j is not None:
                scanner_graph[i][j] = new_j
                # print(f"  {i}/{j}: {new_j}")

# Keep reorienting all other scanners in terms of scanner[0]
while len(scanner_graph[0]) < len(scanners):
    # Identify scanners not yet reachable from [0], but reachable from one of
    # [0]'s connections:
    unreached = {i for i in range(len(scanners)) if i not in scanner_graph[0]}
    reached = {i for i in range(len(scanners)) if i in scanner_graph[0]}
    for i in reached:
        first = scanner_graph[0][i]
        for j in unreached:
            with suppress(KeyError):
                second = scanner_graph[i][j]
                reoriented = first.reorient(second)
                assert reoriented is not None
                scanner_graph[0][j] = reoriented
                # print(f"* 0/{j}: {reoriented}")

normalized_scanners = [scanner_graph[0][i] for i in range(len(scanners))]

# Part 1: How many beacons in total
print(len(set.union(*[scanner.beacons for scanner in normalized_scanners])))

# Part 2: What is the largest Manhattan distance between any two scanners?
print(max(a.pos.mhdist(b.pos) for a, b in combinations(normalized_scanners, 2)))
