from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from math import ceil, floor
from rich import print
from string import digits
from typing import Callable, Iterable


@dataclass(frozen=True)
class Num:
    v: int | tuple[Num, Num]

    @classmethod
    def parse(cls, s: str) -> Num:
        def token(s: str) -> tuple[str, str]:
            if s[0] in "[,]":
                return s[0], s[1:]
            else:
                num_digits = len(s) - len(s.lstrip(digits))
                return s[:num_digits], s[num_digits:]

        def parse_int_or_Num(s: str) -> tuple[Num, str]:
            first, s = token(s)
            if first == "[":
                a, s = parse_int_or_Num(s)
                comma, s = token(s)
                assert comma == ","
                b, s = parse_int_or_Num(s)
                end, s = token(s)
                assert end == "]"
                return cls((a, b)), s
            else:
                return cls(int(first)), s

        num, rest = parse_int_or_Num(s)
        assert isinstance(num, cls) and rest == "", f"{num!r}, {rest!r}"
        return num

    def __str__(self) -> str:
        if isinstance(self.v, int):
            return f"{self.v}"
        else:
            return f"[{self.v[0]},{self.v[1]}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Num):
            return NotImplemented
        return self.v == other.v

    def __add__(self, other: Num) -> Num:
        return self.__class__((self, other)).reduce()

    def dfs_visit(
        self, visitor: Callable[[Num, str], Num], path: str = ""
    ) -> Num:
        if isinstance(self.v, int):
            return visitor(self, path)
        else:
            x, y = self.v
            x = x.dfs_visit(visitor, path + "l")
            y = y.dfs_visit(visitor, path + "r")
            return visitor(self.__class__((x, y)), path)

    @staticmethod
    def left_of(path: str) -> str | None:
        try:
            i = path.rindex("r")
            return path[:i] + "lR"  # apply to right-most node in left sibling
        except ValueError:  # no position to the left of this node
            return None

    @staticmethod
    def right_of(path: str) -> str | None:
        try:
            i = path.rindex("l")
            return path[:i] + "rL"  # Apply to left-most node in right sibling
        except ValueError:  # no position to the right of this node
            return None

    def explode(self) -> Num:
        edits: dict[str, int] = {}
        exploded = False

        def exploder(num: Num, path: str) -> Num:
            nonlocal exploded
            if not exploded and len(path) >= 4 and isinstance(num.v, tuple):
                exploded = True
                assert isinstance(num.v[0].v, int)
                assert isinstance(num.v[1].v, int)
                lpath = num.left_of(path)
                if lpath is not None:
                    edits[lpath] = num.v[0].v
                rpath = num.right_of(path)
                if rpath is not None:
                    edits[rpath] = num.v[1].v
                num = Num(0)
            return num

        def apply_edits(num: Num, path: str) -> Num:
            if isinstance(num.v, int):  # Node can be edited
                # Try to find matching edit
                v = None
                for p in edits.keys():
                    assert p.endswith(("L", "R"))
                    if path.startswith(p[:-1]) and all(
                        c == p[-1].lower() for c in path[len(p) - 1 :]
                    ):
                        v = edits.pop(p)
                        break
                if v is not None:
                    assert isinstance(num.v, int)
                    num = Num(num.v + v)
            return num

        ret = self.dfs_visit(exploder)
        # print(f"  {self} exploded with {edits}")
        while edits:
            pre = edits.copy()
            ret = ret.dfs_visit(apply_edits)
            assert pre != edits
        return ret

    def split(self) -> Num:
        splitted = False

        def splitter(num: Num, path: str) -> Num:
            nonlocal splitted
            if splitted is False and isinstance(num.v, int) and num.v >= 10:
                splitted = True
                # print(f"  {num} splits {num.v} @{path}")
                num = Num((Num(floor(num.v / 2)), Num(ceil(num.v / 2))))
            return num

        return self.dfs_visit(splitter)

    def reduce(self) -> Num:
        ret = self.explode()
        if ret == self:
            ret = self.split()
            if ret == self:
                return self
        return ret.reduce()

    def magnitude(self) -> int:
        if isinstance(self.v, tuple):
            return 3 * self.v[0].magnitude() + 2 * self.v[1].magnitude()
        else:
            return self.v

    @staticmethod
    def sum(nums: Iterable[Num]) -> Num:
        nums = iter(nums)
        ret = next(nums)
        for num in nums:
            ret += num
        return ret


with open("18.input") as f:
    nums = [Num.parse(line.rstrip()) for line in f]

# Part 1: What is the magnitude of the final sum?
print(Num.sum(nums).magnitude())

# Part 2: What is the largest magnitude from adding any two numbers together?
pairs = permutations(nums, 2)
print(max(Num.sum(pair).magnitude() for pair in pairs))


# Unit tests


def test_parse():
    vectors = [
        "[1,2]",
        "[[1,2],3]",
        "[9,[8,7]]",
        "[[1,9],[8,5]]",
        "[[[[1,2],[3,4]],[[5,6],[7,8]]],9]",
        "[[[9,[3,8]],[[0,9],6]],[[[3,7],[4,9]],3]]",
        "[[[[1,3],[5,3]],[[1,3],[8,7]]],[[[4,9],[6,9]],[[8,2],[7,3]]]]",
    ]
    for v in vectors:
        assert str(Num.parse(v)) == v


def test_explode():
    vectors = [
        ("[[[[[9,8],1],2],3],4]", "[[[[0,9],2],3],4]"),
        ("[7,[6,[5,[4,[3,2]]]]]", "[7,[6,[5,[7,0]]]]"),
        ("[[6,[5,[4,[3,2]]]],1]", "[[6,[5,[7,0]]],3]"),
        (
            "[[3,[2,[1,[7,3]]]],[6,[5,[4,[3,2]]]]]",
            "[[3,[2,[8,0]]],[9,[5,[4,[3,2]]]]]",
        ),
        ("[[3,[2,[8,0]]],[9,[5,[4,[3,2]]]]]", "[[3,[2,[8,0]]],[9,[5,[7,0]]]]"),
    ]
    for vin, vout in vectors:
        assert Num.parse(vin).explode() == Num.parse(vout)


def test_add_then_reduce():
    result = Num.parse("[[[[4,3],4],4],[7,[[8,4],9]]]") + Num.parse("[1,1]")
    assert result == Num.parse("[[[[0,7],4],[[7,8],[6,0]]],[8,1]]")


def test_simple_sums():
    def sum_and_test(nums, expect):
        assert Num.sum(Num.parse(n) for n in nums) == Num.parse(expect)

    nums = ["[1,1]", "[2,2]", "[3,3]", "[4,4]"]
    sum_and_test(nums, "[[[[1,1],[2,2]],[3,3]],[4,4]]")

    nums += ["[5,5]"]
    sum_and_test(nums, "[[[[3,0],[5,3]],[4,4]],[5,5]]")

    nums += ["[6,6]"]
    sum_and_test(nums, "[[[[5,0],[7,4]],[5,5]],[6,6]]")


def test_first_nontrivial_sum():
    n1 = Num.parse("[[[0,[4,5]],[0,0]],[[[4,5],[2,6]],[9,5]]]")
    assert n1.reduce() == n1
    n2 = Num.parse("[7,[[[3,7],[4,3]],[[6,3],[8,8]]]]")
    assert n2.reduce() == n2
    expect = Num.parse(
        "[[[[4,0],[5,4]],[[7,7],[6,0]]],[[8,[7,7]],[[7,9],[5,0]]]]"
    )
    assert expect.reduce() == expect
    n3 = Num((n1, n2))
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.split()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))
    n3 = n3.explode()
    print(str(n3))

    print()
    result = n1 + n2
    print(str(result))
    print(str(expect))


def test_nontrivial_sums():
    vectors = [
        ("[[[0,[4,5]],[0,0]],[[[4,5],[2,6]],[9,5]]]", None),
        (
            "[7,[[[3,7],[4,3]],[[6,3],[8,8]]]]",
            "[[[[4,0],[5,4]],[[7,7],[6,0]]],[[8,[7,7]],[[7,9],[5,0]]]]",
        ),
        (
            "[[2,[[0,8],[3,4]]],[[[6,7],1],[7,[1,6]]]]",
            "[[[[6,7],[6,7]],[[7,7],[0,7]]],[[[8,7],[7,7]],[[8,8],[8,0]]]]",
        ),
        (
            "[[[[2,4],7],[6,[0,5]]],[[[6,8],[2,8]],[[2,1],[4,5]]]]",
            "[[[[7,0],[7,7]],[[7,7],[7,8]]],[[[7,7],[8,8]],[[7,7],[8,7]]]]",
        ),
        (
            "[7,[5,[[3,8],[1,4]]]]",
            "[[[[7,7],[7,8]],[[9,5],[8,7]]],[[[6,8],[0,8]],[[9,9],[9,0]]]]",
        ),
        (
            "[[2,[2,2]],[8,[8,1]]]",
            "[[[[6,6],[6,6]],[[6,0],[6,7]]],[[[7,7],[8,9]],[8,[8,1]]]]",
        ),
        ("[2,9]", "[[[[6,6],[7,7]],[[0,7],[7,7]]],[[[5,5],[5,6]],9]]"),
        (
            "[1,[[[9,3],9],[[9,0],[0,7]]]]",
            "[[[[7,8],[6,7]],[[6,8],[0,8]]],[[[7,7],[5,0]],[[5,5],[5,6]]]]",
        ),
        (
            "[[[5,[7,4]],7],1]",
            "[[[[7,7],[7,7]],[[8,7],[8,7]]],[[[7,0],[7,7]],9]]",
        ),
        (
            "[[[[4,2],2],6],[8,7]]",
            "[[[[8,7],[7,7]],[[8,6],[7,7]]],[[[0,7],[6,6]],[8,7]]]",
        ),
    ]
    for i, (v, expect) in enumerate(vectors):
        if expect is None:
            expect = v
        parsed_operands = [Num.parse(vectors[j][0]) for j in range(i + 1)]
        assert Num.sum(parsed_operands) == Num.parse(expect)


def test_magnitude():
    vectors = [
        ("[9,1]", 29),
        ("[[1,2],[[3,4],5]]", 143),
        ("[[[[0,7],4],[[7,8],[6,0]]],[8,1]]", 1384),
        ("[[[[1,1],[2,2]],[3,3]],[4,4]]", 445),
        ("[[[[3,0],[5,3]],[4,4]],[5,5]]", 791),
        ("[[[[5,0],[7,4]],[5,5]],[6,6]]", 1137),
        ("[[[[8,7],[7,7]],[[8,6],[7,7]]],[[[0,7],[6,6]],[8,7]]]", 3488),
    ]
    for v, expect in vectors:
        assert Num.parse(v).magnitude() == expect


def test_sum_and_magnitude():
    addends = [
        "[[[0,[5,8]],[[1,7],[9,6]]],[[4,[1,2]],[[1,4],2]]]",
        "[[[5,[2,8]],4],[5,[[9,9],0]]]",
        "[6,[[[6,2],[5,6]],[[7,6],[4,7]]]]",
        "[[[6,[0,7]],[0,9]],[4,[9,[9,0]]]]",
        "[[[7,[6,4]],[3,[1,3]]],[[[5,5],1],9]]",
        "[[6,[[7,3],[3,2]]],[[[3,8],[5,7]],4]]",
        "[[[[5,4],[7,7]],8],[[8,3],8]]",
        "[[9,3],[[9,9],[6,[4,9]]]]",
        "[[2,[[7,7],7]],[[5,8],[[9,3],[0,2]]]]",
        "[[[[5,2],5],[8,[3,7]]],[[5,[7,5]],[4,4]]]",
    ]
    expect_sum = "[[[[6,6],[7,6]],[[7,7],[7,0]]],[[[7,7],[7,7]],[[7,8],[9,9]]]]"
    expect_magnitude = 4140
    result = Num.sum(Num.parse(s) for s in addends)
    assert result == Num.parse(expect_sum)
    assert result.magnitude() == expect_magnitude


def test():
    test_parse()
    test_explode()
    test_add_then_reduce()
    test_simple_sums()
    # test_first_nontrivial_sum()
    test_nontrivial_sums()
    test_magnitude()
    test_sum_and_magnitude()


test()
