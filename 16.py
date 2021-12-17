from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from math import prod
from operator import eq, gt, lt
from rich import print
from typing import Callable, Iterable, Iterator

ValueCalculator = Callable[[Iterable[int]], int]


@dataclass
class Packet:
    version: int
    type_id: int
    value: int = 0
    subs: list[Packet] = field(default_factory=list)

    def parse_literal(self, bits: str) -> str:
        value = ""
        while True:
            cur, bits = bits[:5], bits[5:]
            value += cur[1:]
            if cur.startswith("0"):
                break
        self.value = int(value, 2)
        return bits

    def parse_operator(self, func: ValueCalculator, bits: str) -> str:
        if bits[0] == "0":  # length type ID: 0
            length = int(bits[1:16], 2)
            self.subs = self.parse_all(bits[16 : 16 + length])
            bits = bits[16 + length :]
        else:  # length type ID: 1
            num_packets = int(bits[1:12], 2)
            bits = bits[12:]
            while num_packets > 0:
                packet, bits = self.parse_one(bits)
                self.subs.append(packet)
                num_packets -= 1
        self.value = func(p.value for p in self.subs)
        return bits

    @staticmethod
    def binary_operator(bin_op: Callable[[int, int], int]) -> ValueCalculator:
        def op_func(args: Iterable[int]) -> int:
            lhs, rhs = list(args)
            return int(bin_op(lhs, rhs))

        return op_func

    @classmethod
    def parse_one(cls, bits: str) -> tuple[Packet, str]:
        packet = cls(int(bits[:3], 2), int(bits[3:6], 2))
        types: dict[int, Callable[[str], str]] = {
            0: partial(packet.parse_operator, sum),
            1: partial(packet.parse_operator, prod),
            2: partial(packet.parse_operator, min),
            3: partial(packet.parse_operator, max),
            4: packet.parse_literal,
            5: partial(packet.parse_operator, cls.binary_operator(gt)),
            6: partial(packet.parse_operator, cls.binary_operator(lt)),
            7: partial(packet.parse_operator, cls.binary_operator(eq)),
        }
        return packet, types[packet.type_id](bits[6:])

    @classmethod
    def parse_all(cls, bits: str) -> list[Packet]:
        packets = []
        while bits:
            packet, bits = cls.parse_one(bits)
            packets.append(packet)
        return packets

    def __iter__(self) -> Iterator[Packet]:
        yield self
        for p in self.subs:
            yield from iter(p)


with open("16.input") as f:
    hex = f.read().rstrip()
    blen = 4 * len(hex)
    bits = f"{int(hex, 16):{blen}b}"
    assert len(bits) % 4 == 0

packet, rest = Packet.parse_one(bits)

# Part 1: What is the sum of the version numbers in all packets?
print(sum(p.version for p in packet))

# Part 2: Evaluate the expression represented by your input
print(packet.value)
