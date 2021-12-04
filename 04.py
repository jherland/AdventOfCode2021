from contextlib import suppress

from rich import print


class Board:
    Rows, Cols = 5, 5

    @classmethod
    def parse(cls, lines):
        rows = []
        for r in range(cls.Rows):
            line = next(lines)
            row = [int(n) for n in line.split()]
            assert len(row) == cls.Cols
            rows.append(row)
        return cls(rows)

    @classmethod
    def parse_multiple(cls, lines):
        with suppress(StopIteration):
            while True:
                assert next(lines).strip() == ""
                yield cls.parse(lines)

    def __init__(self, rows):
        assert len(rows) == self.Rows
        assert all(len(row) == self.Cols for row in rows)
        self.rows = rows
        self.seen = set()
        self.last_draw = None

    def __str__(self):
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
    def cols(self):
        return [list(col) for col in zip(*self.rows)]

    @property
    def nums(self):
        return set(n for row in self.rows for n in row)

    def draw(self, n):
        self.seen.add(n)
        self.last_draw = n

    def has_bingo(self):
        return any(
            all(n in self.seen for n in line) for line in self.rows + self.cols
        )

    def score(self):
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
