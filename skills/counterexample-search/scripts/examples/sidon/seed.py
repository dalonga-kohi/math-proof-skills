def construct():
    """Greedy Sidon set in {1..1000}: a weak but valid starting point."""
    N, A, sums = 1000, [], set()
    for x in range(1, N + 1):
        new = {x + a for a in A} | {2 * x}
        if not (new & sums):
            A.append(x)
            sums |= new
    return A
