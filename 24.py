from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, replace
from functools import partial
import operator
from rich import print
from typing import Callable, Iterator


@dataclass(slots=True)
class ALU:
    w: int = 0
    x: int = 0
    y: int = 0
    z: int = 0
    ip: int = 0

    def inp(self, a: str, val: str) -> None:
        assert val in set("123456789")
        setattr(self, a, int(val))
        self.ip += 1

    def bin_op(self, func: Callable[[int, int], int], a: str, b: str) -> None:
        av = getattr(self, a)
        if b in "wxyz":
            bv = getattr(self, b)
        else:
            bv = int(b)
        setattr(self, a, func(av, bv))
        self.ip += 1

    def __call__(self, input: Iterator[str], *words: str) -> None:
        instr, *args = words
        dispatch: dict[str, Callable[[str], None]] = {
            "inp": lambda a: self.inp(a, next(input)),
            "add": partial(self.bin_op, operator.add),
            "mul": partial(self.bin_op, operator.mul),
            "div": partial(self.bin_op, lambda a, b: int(a / b)),
            "mod": partial(self.bin_op, operator.mod),
            "eql": partial(self.bin_op, lambda a, b: int(a == b)),
        }
        dispatch[instr](*args)

    def run(self, program: list[list[str]], input: Iterator[str]) -> ALU:
        """Run the given program until completion, or until input is exhausted.

        Return the ALU resulting from the last executed instruction.
        """
        alu = replace(self)
        with suppress(StopIteration):
            while alu.ip < len(program):
                alu(input, *program[alu.ip])
        return alu


def find_max_min_model_number(program: list[list[str]]) -> tuple[ALU, str, str]:
    """Find the largest/smallest 14-digit model number that yields alu.z == 0.

    We really only want to keep track of the alu.z value resulting for each
    digit we input. In the observed program, the alu.z value captures the
    salient state of the program between input digits, and for each digit we
    input, alu.z changes in one of two ways:
     - decrease by a factor of 26 (based on 'c1 < 0' - a program constant)
     - increase by a factor of 26 (if 'z % 26 + c1' does not match our input)
    alu.z can - at best - decrease by a factor of 26 for each digit input, hence
    we know that if there are n digits left to input, and alu.z is already
    larger than 26 ** n, then it will never reach zero.
    Furthermore, many different input digits result in the same alu.z. Thus we
    can get away with only storing the max/min input value so far for each
    recorded z between input digits.
    """

    def test_next_digit(alu):
        return [(s, alu.run(program, iter([s]))) for s in "123456789"]

    # Map each z value to a corresponding ALU state and max/min input strings
    z_states: dict[int, tuple[ALU, str, str]] = {0: (ALU(), "", "")}
    for n in range(1, 15):
        max_z = 26 ** (14 - n)  # Z values above this can never reach zero
        # print(f"Trying digit #{n} w/{len(z_states)} states ({max_z=}).")
        z_next: dict[int, tuple[ALU, str, str]] = {}  # z_states, next iteration
        for alu, max_num, min_num in z_states.values():
            for d, alu_next in test_next_digit(alu):
                if alu_next.z > max_z:
                    continue
                _, pmax, pmin = z_next.get(alu_next.z, (None, "1" * n, "9" * n))
                res = (alu_next, max(max_num + d, pmax), min(min_num + d, pmin))
                z_next[alu_next.z] = res
        z_states = z_next
    # print(f"At end there are {len(z_states)} states remaining.")
    # print(z_states)
    return z_states[0]


with open("24.input") as f:
    program = [line.split() for line in f]

alu, max_num, min_num = find_max_min_model_number(program)
# print(alu)
print(max_num)
print(min_num)
