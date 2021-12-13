from collections import Counter

with open("06.input") as f:
    fishes = Counter([int(n) for n in f.read().strip().split(",")])


def next_day(fishes: Counter[int]) -> Counter[int]:
    ret: Counter[int] = Counter()
    for n, count in fishes.most_common():
        if n > 0:
            ret[n - 1] += count
        else:
            ret[6] += count  # reset parents
            ret[8] += count  # add children
    return ret


# Part 1: How many fishes after 80 days
for _ in range(80):
    fishes = next_day(fishes)
print(fishes.total())  # type: ignore

# Part 1: How many fishes after 256 days
for _ in range(256 - 80):
    fishes = next_day(fishes)
print(fishes.total())  # type: ignore
