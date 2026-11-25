"""Trusted evaluator. Keep it short enough to audit line by line."""
N = 1000


def score(obj):
    if not isinstance(obj, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in obj):
        raise ValueError("expected a list of ints")
    A = sorted(set(obj))
    if len(A) != len(obj):
        raise ValueError("duplicates")
    if A and (A[0] < 1 or A[-1] > N):
        raise ValueError("out of range")
    sums = set()
    for i, a in enumerate(A):
        for b in A[i:]:
            if a + b in sums:
                raise ValueError(f"repeated sum {a + b}")
            sums.add(a + b)
    return len(A)
