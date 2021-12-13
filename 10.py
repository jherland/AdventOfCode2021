from collections import Counter


# Map brackets both ways
open_brackets = {"(": ")", "[": "]", "{": "}", "<": ">"}
close_brackets = {b: a for a, b in open_brackets.items()}


def parse_line(line: str) -> tuple[list[str], list[str]]:
    symbols = list(line)
    stack = []
    while symbols:
        c = symbols.pop(0)
        if c in open_brackets:
            stack.append(c)
            continue
        elif c in close_brackets:
            if stack[-1] == close_brackets[c]:  # matching bracket
                stack.pop()
                continue
            else:  # non-matching bracket
                symbols.insert(0, c)  # un-pop current symbol
                break
        else:  # invalid symbol
            raise ValueError(f"Invalid symbol {c!r} in {line!r}!")

    return symbols, stack


def completion_score(stack: list[str]) -> int:
    completion = [open_brackets[c] for c in reversed(stack)]
    score = 0
    char_score = {")": 1, "]": 2, "}": 3, ">": 4}
    for c in completion:
        score = 5 * score + char_score[c]
    return score


with open("10.input") as f:
    lines = [parse_line(line.rstrip()) for line in f]

# Part 1: What is the total syntax error score for the corrupted lines?
corrupt_score = {")": 3, "]": 57, "}": 1197, ">": 25137}
corruptions = Counter([symbols[0] for symbols, _ in lines if symbols])
print(sum(corruptions[c] * score for c, score in corrupt_score.items()))

# Part 2: What is the middle score of the completion strings?
incomplete = [stack for symbols, stack in lines if stack and not symbols]
completion_scores = sorted([completion_score(stack) for stack in incomplete])
print(completion_scores[len(completion_scores) // 2])
