import time

# Development tools used in place of timeit (no micropython equivalent)
# Useful to measure performance changes while refactoring


# Pass callable as call, no ()
def timetest(call, runs=5):
    count = 0

    # The function takes this long to run an empty call, so it needs to be subtracted from runtime
    overhead = 0.0024

    times = []

    while count < runs:
        start = time.time_ns()
        call()
        end = time.time_ns()
        times.append((end - start) / 1000000000)
        count = count + 1
        print(f"Run time = {(end - start) / 1000000000} seconds")

    total = 0
    for i in times:
        total = total + i

    avg = total / len(times) - overhead
    print(f"Avg run time = {avg}, n = {runs}")


def compare(old, new):
    print(f"New was {old - new} seconds faster ({round((old - new) / old * 100, 2)}%) than Old")
