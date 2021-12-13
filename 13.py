from rich import print


def parse_dot(line):
    match line.rstrip().split(","):
        case [x, y]:
            return int(x), int(y)
        case _:
            raise ValueError(repr(line))


def parse_fold(line):
    match line.rstrip().split("="):
        case ["fold along x", n]:
            return int(n), None
        case ["fold along y", n]:
            return None, int(n)
        case _:
            raise ValueError(repr(line))


def parse(lines):
    dots = set()
    for line in lines:
        if not line.rstrip():
            break
        dots.add(parse_dot(line))
    folds = [parse_fold(line) for line in lines]
    return dots, folds


def fold(dots, fx, fy):
    assert fx is None or fy is None
    if fx is None:  # fold up everything below given y
        for x, y in dots:
            if y <= fy:
                yield x, y
            else:
                yield x, fy - (y - fy)
    if fy is None:
        for x, y in dots:
            if x <= fx:
                yield x, y
            else:
                yield fx - (x - fx), y


def render(dots):
    xs, ys = zip(*dots)
    width = max(xs)
    height = max(ys)
    for y in range(height + 1):
        for x in range(width + 1):
            print("#" if (x, y) in dots else " ", end="")
        print()


with open("13.input") as f:
    dots, folds = parse(f)

# Part 1: How many dots are visible after completing the first fold instruction?
print(len(set(fold(dots, *folds[0]))))

# Part 2: Render the code visible after completing all folds
for f in folds:
    dots = set(fold(dots, *f))
render(dots)
