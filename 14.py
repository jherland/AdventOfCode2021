from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from functools import reduce
from itertools import pairwise
from rich import print
from typing import Iterator


@dataclass
class Polymer:
    reactions: dict[str, str]
    pairs: Counter[str]  # count pairs
    last: str  # keep track of last pair

    @staticmethod
    def parse_reaction(line: str) -> tuple[str, str]:
        src, arrow, dst = line.rstrip().split()
        assert arrow == "->"
        assert len(src) == 2
        assert len(dst) == 1
        return src, f"{src[0]}{dst}{src[1]}"

    @staticmethod
    def pairwise(s: str) -> list[str]:
        return ["".join(chars) for chars in pairwise(s)]

    @classmethod
    def parse(cls, lines: Iterator[str]) -> Polymer:
        s = next(lines).rstrip()
        assert next(lines).rstrip() == ""
        reactions = dict(cls.parse_reaction(line) for line in lines)
        return cls(reactions, Counter(cls.pairwise(s)), s[-2:])

    def react(self) -> Polymer:
        new_polymer: Counter[str] = Counter()
        for pair, count in self.pairs.items():
            a, b = self.pairwise(self.reactions[pair])  # post-reaction pairs
            new_polymer[a] += count
            new_polymer[b] += count
        new_last = self.reactions[self.last][-2:]
        return self.__class__(self.reactions, new_polymer, new_last)

    def react_n(self, n: int) -> Polymer:
        return reduce(lambda s, _: s.react(), range(n), self)

    def most_common_elements(self) -> list[tuple[str, int]]:
        elements: Counter[str] = Counter()
        for pair, count in self.pairs.items():
            elements[pair[0]] += count  # count first char from all pairs
        elements[self.last[-1]] += 1  # count last char from last pair
        return elements.most_common()


with open("14.input") as f:
    polymer = Polymer.parse(f)

# Part 1: # of most common minus # of least common element after 10 steps
most, *_, least = polymer.react_n(10).most_common_elements()
print(most[1] - least[1])

# Part 2: # of most common minus # of least common element after 40 steps
most, *_, least = polymer.react_n(40).most_common_elements()
print(most[1] - least[1])
