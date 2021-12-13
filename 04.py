from __future__ import annotations
from contextlib import suppress
from rich import print
from typing import Iterator


class Board:
    Rows, Cols = 5, 5

    @classmethod
    def parse(cls, lines: Iterator[str]) -> Board:
        rows = []
        for r in range(cls.Rows):
            line = next(lines)
            row = [int(n) for n in line.split()]
            assert len(row) == cls.Cols
            rows.append(row)
        return cls(rows)

    @classmethod
    def parse_multiple(cls, lines: Iterator[str]) -> Iterator[Board]:
        with suppress(StopIteration):
            while True:
                assert next(lines).strip() == ""
                yield cls.parse(lines)

    def __init__(self, rows: list[list[int]]):
        assert len(rows) == self.Rows
        assert all(len(row) == self.Cols for row in rows)
        self.rows: list[list[int]] = rows
        self.seen: set[int] = set()
        self.last_draw: int | None = None

    def __str__(self) -> str:
        ret = []
        for row in self.rows:
            for n in row:
                s = f" {n:2d}"
                if n in self.seen:
                    s = f"[bold red]{s}[/]"
                ret.append(s)
            ret.append("\n")
        return "".join(ret)

    @property
    def cols(self) -> list[list[int]]:
        return [list(col) for col in zip(*self.rows)]

    @property
    def nums(self) -> set[int]:
        return set(n for row in self.rows for n in row)

    def draw(self, n: int) -> None:
        self.seen.add(n)
        self.last_draw = n

    def has_bingo(self) -> bool:
        return any(
            all(n in self.seen for n in line) for line in self.rows + self.cols
        )

    def score(self) -> int:
        assert self.last_draw is not None
        return sum(self.nums - self.seen) * self.last_draw


with open("04.input") as f:
    nums = [int(n) for n in next(f).split(",")]
    boards = list(Board.parse_multiple(f))

first_winner, last_winner = None, None
for n in nums:
    # print(f"Drew {n}")
    for b in boards:
        if not b.has_bingo():
            b.draw(n)
            if b.has_bingo():
                # print("BINGO!")
                # print(str(b))
                # print(b.score())
                if first_winner is None:
                    first_winner = b.score()
                last_winner = b.score()

# Part 1/2: Score of first/last board to win
print(first_winner)
print(last_winner)
