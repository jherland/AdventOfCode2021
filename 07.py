def linear_cost(steps):
    return steps


def triangular_cost(steps):
    return steps * (steps + 1) // 2


def fuel_used(crabs, position, cost_func):
    return sum(cost_func(abs(c - position)) for c in crabs)


def minimize_total_fuel_usage(crabs, cost_func):
    return min(
        fuel_used(crabs, p, cost_func)
        for p in range(min(crabs), max(crabs) + 1)
    )


with open("07.input") as f:
    crabs = [int(n) for n in f.read().strip().split(",")]

# Part 1: Minimize fuel usage with linear cost
print(minimize_total_fuel_usage(crabs, linear_cost))

# Part 2: Minimize fuel usage with triangular cost
print(minimize_total_fuel_usage(crabs, triangular_cost))
