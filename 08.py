from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Segments:
    letters: str

    @classmethod
    def parse(cls, word: str) -> Segments:
        return cls("".join(sorted(word)))

    def __repr__(self) -> str:
        return f"<{self.letters}>"

    def __len__(self) -> int:
        return len(self.letters)

    def __and__(self, other: Segments) -> Segments:
        return self.__class__(
            "".join(sorted(set(self.letters) & set(other.letters)))
        )

    def __or__(self, other: Segments) -> Segments:
        return self.__class__(
            "".join(sorted(set(self.letters) | set(other.letters)))
        )

    def __xor__(self, other: Segments) -> Segments:
        return self.__class__(
            "".join(sorted(set(self.letters) ^ set(other.letters)))
        )


def parse_line(line: str) -> tuple[set[Segments], list[Segments]]:
    def parse_words(words: str) -> Iterable[Segments]:
        return map(Segments.parse, words.split())

    ten, four = line.split("|")
    return set(parse_words(ten)), list(parse_words(four))


class TwoWayDict(dict[Any, Any]):  # type: ignore
    def __setitem__(self, key: Any, value: Any) -> None:  # type: ignore
        assert key not in self
        assert value not in self
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __len__(self) -> int:
        return dict.__len__(self) // 2


def only(gen: Iterable[T]) -> T:
    one_item_list = list(gen)
    assert len(one_item_list) == 1
    return one_item_list[0]


def decipher(ten_words: set[Segments]) -> TwoWayDict:
    by_len: dict[int, set[Segments]] = {}
    for item in ten_words:
        by_len.setdefault(len(item), set()).add(item)
    assert len(by_len[2]) == 1  # 1
    assert len(by_len[3]) == 1  # 7
    assert len(by_len[4]) == 1  # 4
    assert len(by_len[5]) == 3  # 2, 3, 5
    assert len(by_len[6]) == 3  # 0, 6, 9
    assert len(by_len[7]) == 1  # 7

    ret = TwoWayDict()

    # add the trivial cases
    ret[1] = only(by_len[2])
    ret[7] = only(by_len[3])
    ret[4] = only(by_len[4])
    ret[8] = only(by_len[7])

    # six letters: 1 is a subset of 0 and 9, but not of 6
    ret[6] = only(s for s in by_len[6] if len(s & ret[1]) < 2)
    by_len[6].remove(ret[6])  # 0 and 9 left

    # five letters: 1 is a subset of 3, but not of 2 and 5
    ret[3] = only(s for s in by_len[5] if len(s & ret[1]) == 2)
    by_len[5].remove(ret[3])  # 2 and 5 left

    # 5 is a subset of 9, but 2 is neither a subset of 0 nor 9
    ret[5], ret[9] = only(
        (seg5, seg6)
        for seg5 in by_len[5]
        for seg6 in by_len[6]
        if len(seg5 & seg6) == 5
    )
    by_len[5].remove(ret[5])
    by_len[6].remove(ret[9])

    # only 2 and 0 remain
    ret[2] = only(by_len[5])
    ret[0] = only(by_len[6])

    return ret


with open("08.input") as f:
    lines = [parse_line(line) for line in f]

digits = []
for ten, four in lines:
    codebook = decipher(ten)
    digits.append([codebook[segments] for segments in four])

# Part 1: How many times do digits 1, 4, 7, 8 appear in the output values?
print(sum(sum(d in {1, 4, 7, 8} for d in dig) for dig in digits))

# Part 2: Add up all the output values
print(sum(int("".join(str(d) for d in dig)) for dig in digits))
