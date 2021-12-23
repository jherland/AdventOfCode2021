from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, replace
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
class Cuboid:
    min: Pos
    max: Pos

    def __post_init__(self):
        diff = self.max - self.min
        if diff.x < 0 or diff.y < 0 or diff.z < 0:
            raise ValueError(f"Cannot create {self} with negative size")

    @classmethod
    def parse(cls, line: str) -> Cuboid:
        components = line.rstrip().split(",")
        min, max = [], []
        for component, c in zip(components, "xyz"):
            component = component.removeprefix(f"{c}=")
            c_min, c_max = [int(num) for num in component.split("..")]
            assert c_min <= c_max
            min.append(c_min)
            max.append(c_max)
        return cls(Pos(*min), Pos(*max))

    def overlap(self, other: Cuboid) -> Cuboid:
        return Cuboid(
            Pos(
                max(self.min.x, other.min.x),
                max(self.min.y, other.min.y),
                max(self.min.z, other.min.z),
            ),
            Pos(
                min(self.max.x, other.max.x),
                min(self.max.y, other.max.y),
                min(self.max.z, other.max.z),
            ),
        )

    def s_overlap(self, other: Cuboid) -> Cuboid | None:
        with suppress(ValueError):
            return self.overlap(other)
        return None

    def size(self):
        diff = self.max - self.min
        return (diff.x + 1) * (diff.y + 1) * (diff.z + 1)

    def split(self, **plane: int) -> tuple[Cuboid, Cuboid]:
        """Split this cuboid in two, along the dim=val plane.

        The given val becomes part of the second/right-hand cuboid.
        """
        assert len(plane) == 1
        dim, val = plane.popitem()
        assert dim in "xyz"
        min_d, max_d = getattr(self.min, dim), getattr(self.max, dim)
        if not min_d < val <= max_d:
            raise ValueError(f"{dim} must be in ({min_d}, {max_d}]")

        a = Cuboid(self.min, replace(self.max, **{dim: val - 1}))
        b = Cuboid(replace(self.min, **{dim: val}), self.max)
        assert self.overlap(a) == a
        assert self.overlap(b) == b
        assert a.s_overlap(b) is None
        assert self.size() == a.size() + b.size()
        return a, b

    def remove(self, other: Cuboid) -> Iterator[Cuboid]:
        """Generate new cuboids that represent self with other removed."""
        try:
            overlap = self.overlap(other)
        except ValueError:  # Trivial case: no overlap -> nothing to remove
            yield self
            return
        # print(f"REMOVE {other} from {self}, overlap is {overlap}")

        # Split along the faces of the overlap and yield sub-cuboids that are
        # disjoint from the overlap, until only the overlap remains
        def flip(pair: tuple[Cuboid, Cuboid]) -> tuple[Cuboid, Cuboid]:
            a, b = pair
            return b, a

        cuts = iter(
            [
                # cut functions return (disjoint, remainder) pairs
                lambda rem: rem.split(x=overlap.min.x),
                lambda rem: rem.split(y=overlap.min.y),
                lambda rem: rem.split(z=overlap.min.z),
                lambda rem: flip(rem.split(x=overlap.max.x + 1)),
                lambda rem: flip(rem.split(y=overlap.max.y + 1)),
                lambda rem: flip(rem.split(z=overlap.max.z + 1)),
            ]
        )
        remainder = self
        while remainder != overlap:  # Still more to cut
            cut = next(cuts)
            # print(f"  Cutting {cut} from {remainder}")
            with suppress(ValueError):
                disjoint, remainder = cut(remainder)
                # print(f"    Yielding {disjoint}, keeping {remainder}")
                yield disjoint

        assert remainder == overlap


class DisjointPieces:
    # TODO: Rewrite to tree structure where we use x/y/z-planes to split pieces
    # and limit traversal length of new additions to O(log(n)) instead of O(n).
    def __init__(self):
        self.pairs: list[tuple[bool, Cuboid]] = []

    def add(self, state: bool, piece: Cuboid) -> None:
        pending_pieces: list[tuple[bool, Cuboid]] = [(state, piece)]
        while pending_pieces:  # repeat until all pieces have been added
            state, piece = pending_pieces.pop(0)
            pairs: list[tuple[bool, Cuboid]] = []
            # print(f"  > Adding {state} {piece} with size {piece.size()}...")
            for i, (i_state, i_piece) in enumerate(self.pairs):
                try:
                    i_piece.overlap(piece)
                except ValueError:  # pieces do not overlap
                    pairs.append(self.pairs[i])  # no change to existing pair
                    continue
                if state == i_state:  # union, can skip adding overlap
                    new_pieces = list(piece.remove(i_piece))
                    # print(f"   Split new piece to {len(new_pieces)} at i={i}")
                    if not new_pieces:  # piece disappeared fully into i_piece
                        pairs.extend(self.pairs[i:])  # shortcut rest of loop
                        break  # and stop this addition
                    pairs.append(self.pairs[i])  # no change to existing pair
                    piece = new_pieces.pop(0)  # keep adding largest piece
                    # and add the other pieces later
                    pending_pieces.extend((state, p) for p in new_pieces)
                    continue
                else:  # difference, must remove overlap from i_piece
                    new_i_pieces = list(i_piece.remove(piece))
                    # print(f"   Split existing piece into {len(new_i_pieces)}")
                    pairs.extend((i_state, i_p) for i_p in new_i_pieces)
                    continue
            else:
                # print(f"  - Append {state} {piece} with size {piece.size()}")
                pairs.append((state, piece))  # Add remaining piece to the end

            # print(f"  < Replace {len(self.pairs)} with {len(pairs)} pairs")
            self.pairs = pairs

    def __iter__(self) -> Iterator[tuple[bool, Cuboid]]:
        return iter(self.pairs)


def parse_line(line: str) -> tuple[bool, Cuboid]:
    word, rest = line.split(" ", 1)
    return True if word == "on" else False, Cuboid.parse(rest)


pieces = DisjointPieces()
with open("22.input") as f:
    for line in f:
        word, rest = line.split(" ", 1)
        pieces.add(word == "on", Cuboid.parse(rest))

# Part 1: How many cubes are on after the initialization procedure?
init_cube = Cuboid(Pos(-50, -50, -50), Pos(50, 50, 50))
init_pieces = [p for s, p in pieces if s and p.s_overlap(init_cube) is not None]
print(sum(piece.size() for piece in init_pieces))

# Part 2: How many cubes are on after all steps?
print(sum(piece.size() for state, piece in pieces if state))


# Unit tests


def test_cuboid_split():
    a = Cuboid(Pos(0, 0, 0), Pos(10, 10, 10))
    try:
        a.split(x=0)
    except ValueError:
        pass
    else:
        assert False

    b, c = a.split(x=1)
    assert b == Cuboid(Pos(0, 0, 0), Pos(0, 10, 10))
    assert c == Cuboid(Pos(1, 0, 0), Pos(10, 10, 10))

    b, c = a.split(x=10)
    assert b == Cuboid(Pos(0, 0, 0), Pos(9, 10, 10))
    assert c == Cuboid(Pos(10, 0, 0), Pos(10, 10, 10))

    try:
        a.split(x=11)
    except ValueError:
        pass
    else:
        assert False

    b, c = a.split(y=5)
    assert b == Cuboid(Pos(0, 0, 0), Pos(10, 4, 10))
    assert c == Cuboid(Pos(0, 5, 0), Pos(10, 10, 10))

    b, c = a.split(z=5)
    assert b == Cuboid(Pos(0, 0, 0), Pos(10, 10, 4))
    assert c == Cuboid(Pos(0, 0, 5), Pos(10, 10, 10))


def test_cuboid_remove():
    a = Cuboid(Pos(0, 0, 0), Pos(10, 10, 10))

    # Disjoint
    assert list(a.remove(Cuboid(Pos(11, 0, 0), Pos(21, 10, 10)))) == [a]

    # Exact overlap
    assert list(a.remove(Cuboid(Pos(0, 0, 0), Pos(10, 10, 10)))) == []

    # Remove last half
    r = Cuboid(Pos(5, 0, 0), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(0, 0, 0), Pos(4, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first half
    r = Cuboid(Pos(0, 0, 0), Pos(4, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(5, 0, 0), Pos(10, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove last quarter
    r = Cuboid(Pos(5, 5, 0), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(0, 0, 0), Pos(4, 10, 10)),
        Cuboid(Pos(5, 0, 0), Pos(10, 4, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first quarter
    r = Cuboid(Pos(0, 0, 0), Pos(4, 4, 10))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(5, 0, 0), Pos(10, 10, 10)),
        Cuboid(Pos(0, 5, 0), Pos(4, 10, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove last eighth
    r = Cuboid(Pos(5, 5, 5), Pos(10, 10, 10))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(0, 0, 0), Pos(4, 10, 10)),
        Cuboid(Pos(5, 0, 0), Pos(10, 4, 10)),
        Cuboid(Pos(5, 5, 0), Pos(10, 10, 4)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove first eighth
    r = Cuboid(Pos(0, 0, 0), Pos(4, 4, 4))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(5, 0, 0), Pos(10, 10, 10)),
        Cuboid(Pos(0, 5, 0), Pos(4, 10, 10)),
        Cuboid(Pos(0, 0, 5), Pos(4, 4, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()

    # Remove from center
    r = Cuboid(Pos(3, 3, 3), Pos(7, 7, 7))
    result = list(a.remove(r))
    assert result == [
        Cuboid(Pos(0, 0, 0), Pos(2, 10, 10)),
        Cuboid(Pos(3, 0, 0), Pos(10, 2, 10)),
        Cuboid(Pos(3, 3, 0), Pos(10, 10, 2)),
        Cuboid(Pos(8, 3, 3), Pos(10, 10, 10)),
        Cuboid(Pos(3, 8, 3), Pos(7, 10, 10)),
        Cuboid(Pos(3, 3, 8), Pos(7, 7, 10)),
    ]
    assert sum(c.size() for c in result) + r.size() == a.size()


def test():
    test_cuboid_split()
    test_cuboid_remove()


test()
