from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    y: int
    x: int

    @classmethod
    def parse(cls, s):
        return cls(*map(int, s.split(",")))


def ints_between(a, b):
    step = 1 if a <= b else -1
    yield from range(a, b + step, step)


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point

    @classmethod
    def parse(cls, s):
        match s.split(" "):
            case [p1, "->", p2]:
                return cls(Point.parse(p1), Point.parse(p2))

    def is_horizontal(self):
        return self.start.y == self.end.y

    def is_vertical(self):
        return self.start.x == self.end.x

    def points(self):
        if self.is_horizontal():
            for x in ints_between(self.start.x, self.end.x):
                yield Point(self.start.y, x)
        elif self.is_vertical():
            for y in ints_between(self.start.y, self.end.y):
                yield Point(y, self.start.x)
        else:  # must be diagonal at 45 degrees
            ys = list(ints_between(self.start.y, self.end.y))
            xs = list(ints_between(self.start.x, self.end.x))
            assert len(ys) == len(xs)
            for y, x in zip(ys, xs):
                yield Point(y, x)


def horiz_or_vert(line):
    return line.is_horizontal() or line.is_vertical()


def count_vents(lines, filter=lambda _: True):
    vents = Counter()
    for line in lines:
        if filter(line):
            for point in line.points():
                vents[point] += 1
    return vents.most_common()


with open("05.input") as f:
    lines = [Line.parse(line) for line in f]

# Part 1: At how many points do at least two vertical/horizontal lines overlap?
print(sum(1 for _, count in count_vents(lines, horiz_or_vert) if count >= 2))

# Part 2: At how many points do at least two lines overlap?
print(sum(1 for _, count in count_vents(lines) if count >= 2))
