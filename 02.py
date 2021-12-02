def parse_line(line):
    match line.split():
        case ["forward", n]:
            return (int(n), 0)
        case ["down", n]:
            return (0, int(n))
        case ["up", n]:
            return (0, -int(n))


with open("02.input") as f:
    moves = [parse_line(line) for line in f]

# Part 1: Multiply your final horizontal position by your final depth.
hpos, depth = [sum(ns) for ns in zip(*moves)]  # sum hpos & depth separately
print(hpos * depth)

# Part 2: The up/down value adjusts _aim_, not depth. Redo calculation.
hpos, depth, aim = 0, 0, 0
for d_pos, d_aim in moves:
    hpos += d_pos
    depth += d_pos * aim
    aim += d_aim
print(hpos * depth)
