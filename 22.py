from __future__ import annotations

from contextlib import suppress
from dataclasses import astuple, dataclass, field, replace
from rich import print
from typing import Iterator


@dataclass(frozen=True)
class Pos:
    x: int
    y: int
    z: int

    def __sub__(self, other: Pos) -> Pos:
        return Pos(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass(frozen=True)
class Volume:
    start: Pos  # inclusive
    end: Pos  # exclusive

    @classmethod
    def parse(cls, line: str) -> Volume:
        components = line.rstrip().split(",")
        start, end = [], []
        for component, c in zip(components, "xyz"):
            component = component.removeprefix(f"{c}=")
            c_min, c_max = [int(num) for num in component.split("..")]
            assert c_min <= c_max
            start.append(c_min)
            end.append(c_max + 1)  # Input coords are inclusive, we are excl.
        return cls(Pos(*start), Pos(*end))

    def __post_init__(self):
        diff = self.end - self.start
        if diff.x <= 0 or diff.y <= 0 or diff.z <= 0:
            raise ValueError(f"Cannot create {self} with zero/negative size")

    def size(self) -> int:
        diff = self.end - self.start
        return diff.x * diff.y * diff.z

    def __and__(self, other: Volume) -> Volume:
        return Volume(
            Pos(
                max(self.start.x, other.start.x),
                max(self.start.y, other.start.y),
                max(self.start.z, other.start.z),
            ),
            Pos(
                min(self.end.x, other.end.x),
                min(self.end.y, other.end.y),
                min(self.end.z, other.end.z),
            ),
        )

    def cut(self, flip: bool = False, **plane: int) -> tuple[Volume, Volume]:
        """Split this volume in two, along the given dim=val plane.

        Return the volumes in coordinate order (i.e. the left/front/bottom
        volume first, then the right/back/top volume). If 'flip' is enabled,
        return the volumes in the opposite order.
        """
        dim, val = plane.popitem()
        assert dim in "xyz" and not plane  # only _one_ x/y/z plane given
        start_d, end_d = getattr(self.start, dim), getattr(self.end, dim)
        if not start_d < val < end_d:
            raise ValueError(f"{dim} must be in ({start_d}, {end_d}]")

        a = Volume(self.start, replace(self.end, **{dim: val}))
        b = Volume(replace(self.start, **{dim: val}), self.end)
        return (a, b) if not flip else (b, a)

    def remove(self, other: Volume) -> Iterator[Volume]:
        """Generate new volumes that represent 'self' with 'other' removed."""
        try:
            overlap = self & other
        except ValueError:  # Trivial case: no overlap -> nothing to remove
            yield self
            return

        # Cut along faces of 'overlap' to yield as few cuts as possible
        cuts = [  # Cut functions must return (cut, remainder) in that order
            # X: Cut along left, then right, face of overlap
            lambda remainder: remainder.cut(x=overlap.start.x),
            lambda remainder: remainder.cut(x=overlap.end.x, flip=True),
            # Y: Cut along front, then rear, face of overlap
            lambda remainder: remainder.cut(y=overlap.start.y),
            lambda remainder: remainder.cut(y=overlap.end.y, flip=True),
            # Y: Cut along bottom, then top, face of overlap
            lambda remainder: remainder.cut(z=overlap.start.z),
            lambda remainder: remainder.cut(z=overlap.end.z, flip=True),
        ]
        remainder = self
        for cut in cuts:
            with suppress(ValueError):
                offcut, remainder = cut(remainder)
                yield offcut
        assert remainder == overlap  # sanity check


@dataclass
class Cuboid:
    on: bool
    vol: Volume
    children: list[Cuboid] = field(default_factory=list)

    @classmethod
    def parse(cls, line: str) -> Cuboid:
        word, rest = line.split(" ", 1)
        return cls(word == "on", Volume.parse(rest))

    @classmethod
    def init(cls, r: int, state: bool = False) -> Cuboid:
        return cls(state, Volume(Pos(*([-r] * 3)), Pos(*([r + 1] * 3))))

    def count_on(self) -> int:
        if self.children:  # This cuboid has been split
            return sum(child.count_on() for child in self.children)
        else:
            return self.on * self.vol.size()

    def toggle(self, other: Cuboid) -> None:
        assert not other.children  # not supported
        try:
            overlap = self.vol & other.vol
        except ValueError:  # no overlap
            return

        if self.children:
            for child in self.children:
                child.toggle(other)
        elif other.on != self.on:  # need to (partly) switch state
            self.children = [
                self.__class__(self.on, vol) for vol in self.vol.remove(overlap)
            ]
            if self.children:
                self.children.append(self.__class__(other.on, overlap))
            else:  # other takes over self completely
                assert self.vol == overlap, f"{self} vs {other}"
                self.on = other.on


def reboot(reactor, steps):
    for step in steps:
        reactor.toggle(step)
    return reactor


with open("22.input") as f:
    steps = [Cuboid.parse(line) for line in f]

# Part 1: How many cubes are on after the initialization procedure?
print(reboot(Cuboid.init(50), steps).count_on())

# Part 2: How many cubes are on after all steps?
max_radius = max(
    max(abs(val) for val in [*astuple(s.vol.start), *astuple(s.vol.end)])
    for s in steps
)
print(reboot(Cuboid.init(max_radius), steps).count_on())


# Unit tests


def test_Volume_cut():
    a = Volume(Pos(0, 0, 0), Pos(10, 10, 10))
    try:
        a.cut(x=0)
    except ValueError:
        pass
    else:
        assert False

    b, c = a.cut(x=1)
    assert b == Volume(Pos(0, 0, 0), Pos(1, 10, 10))
    assert c == Volume(Pos(1, 0, 0), Pos(10, 10, 10))

    b, c = a.cut(x=9)
    assert b == Volume(Pos(0, 0, 0), Pos(9, 10, 10))
    assert c == Volume(Pos(9, 0, 0), Pos(10, 10, 10))

    try:
        a.cut(x=10)
    except ValueError:
        pass
    else:
        assert False

    b, c = a.cut(y=5)
    assert b == Volume(Pos(0, 0, 0), Pos(10, 5, 10))
    assert c == Volume(Pos(0, 5, 0), Pos(10, 10, 10))

    b, c = a.cut(z=5)
    assert b == Volume(Pos(0, 0, 0), Pos(10, 10, 5))
    assert c == Volume(Pos(0, 0, 5), Pos(10, 10, 10))


def test_Volume_remove():
    a = Volume(Pos(0, 0, 0), Pos(10, 10, 10))

    # Disjoint
    assert list(a.remove(Volume(Pos(11, 0, 0), Pos(21, 10, 10)))) == [a]

    # Exact overlap
    assert list(a.remove(Volume(Pos(0, 0, 0), Pos(10, 10, 10)))) == []

    # Remove last half
    r = Volume(Pos(5, 0, 0), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(0, 0, 0), Pos(5, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first half
    r = Volume(Pos(0, 0, 0), Pos(5, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(5, 0, 0), Pos(10, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove last quarter
    r = Volume(Pos(5, 5, 0), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(0, 0, 0), Pos(5, 10, 10)),
        Volume(Pos(5, 0, 0), Pos(10, 5, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first quarter
    r = Volume(Pos(0, 0, 0), Pos(5, 5, 10))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(5, 0, 0), Pos(10, 10, 10)),
        Volume(Pos(0, 5, 0), Pos(5, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove last eighth
    r = Volume(Pos(5, 5, 5), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(0, 0, 0), Pos(5, 10, 10)),
        Volume(Pos(5, 0, 0), Pos(10, 5, 10)),
        Volume(Pos(5, 5, 0), Pos(10, 10, 5)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first eighth
    r = Volume(Pos(0, 0, 0), Pos(5, 5, 5))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(5, 0, 0), Pos(10, 10, 10)),
        Volume(Pos(0, 5, 0), Pos(5, 10, 10)),
        Volume(Pos(0, 0, 5), Pos(5, 5, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove from center
    r = Volume(Pos(3, 3, 3), Pos(7, 7, 7))
    result = list(a.remove(r))
    assert result == [
        Volume(Pos(0, 0, 0), Pos(3, 10, 10)),
        Volume(Pos(7, 0, 0), Pos(10, 10, 10)),
        Volume(Pos(3, 0, 0), Pos(7, 3, 10)),
        Volume(Pos(3, 7, 0), Pos(7, 10, 10)),
        Volume(Pos(3, 3, 0), Pos(7, 7, 3)),
        Volume(Pos(3, 3, 7), Pos(7, 7, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()


def test():
    test_Volume_cut()
    test_Volume_remove()


test()
