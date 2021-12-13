from dataclasses import dataclass
from rich import print
from typing import Callable, Iterator


@dataclass(frozen=True)
class Cave:
    name: str
    neighbors: frozenset[str]

    def is_small(self) -> bool:
        return self.name.islower()


class Path(tuple[Cave]):
    def __str__(self) -> str:
        return " -> ".join(cave.name for cave in self)


def at_end(path: Path) -> bool:
    return path[-1].name == "end"


def explore(
    caves: dict[str, Cave],
    start_path: Path,
    follow: Callable[[Path, Cave], bool],
) -> Iterator[Path]:
    assert len(start_path) > 0
    if at_end(start_path):
        yield start_path
    for nbor in start_path[-1].neighbors:
        if follow(start_path, caves[nbor]):
            yield from explore(caves, Path(start_path + (caves[nbor],)), follow)


def follow_part1(path: Path, next_cave: Cave) -> bool:
    visited = {cave.name for cave in path}
    if at_end(path):
        return False  # stop at end cave
    if next_cave.is_small() and next_cave.name in visited:
        return False  # only visit small caves once
    return True


def follow_part2(path: Path, next_cave: Cave) -> bool:
    visited = [cave.name for cave in path if cave.is_small()]
    unique = set(visited)
    if at_end(path):
        return False  # stop at end cave
    if next_cave.name == "start":
        return False  # don't revisit start
    if (
        next_cave.is_small()
        and next_cave.name in unique
        and len(visited) > len(unique)
    ):
        return False  # allow only one revisit to any small cave
    return True


with open("12.input") as f:
    conns: dict[str, set[str]] = {}
    for line in f:
        a, b = line.rstrip().split("-")
        conns.setdefault(a, set()).add(b)
        conns.setdefault(b, set()).add(a)

caves = {name: Cave(name, frozenset(nbors)) for name, nbors in conns.items()}

# Part 1: How many paths that visit small caves at most once?
print(len(list(explore(caves, Path((caves["start"],)), follow_part1))))

# Part 2: How many paths that visit one small cave at most twice?
print(len(list(explore(caves, Path((caves["start"],)), follow_part2))))
