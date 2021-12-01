with open('01.input') as f:
    nums = [int(line) for line in f]

# Part 1: How many measurements are larger than the previous measurement?
print(sum(b > a for a, b in zip(nums, nums[1:])))

# Part 2: How many 3-measurement windows are larger than the previous window?
windows = [sum(abc) for abc in zip(nums, nums[1:], nums[2:])]
print(sum(b > a for a, b in zip(windows, windows[1:])))
