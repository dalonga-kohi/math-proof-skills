#!/usr/bin/env python3
"""Reproduce-known-values harness.

Pattern: two independent implementations of the quantity, a table of values
known from the literature (with sources), and a run that refuses to go past the
known range until both implementations agree with the table everywhere.

Copy this file next to your problem, replace the two `compute_*` functions and
KNOWN, and run:

    python3 harness.py --max-n 12 --json results.json

The shipped example is the maximum size of a Sidon set (all pairwise sums a+b,
a<=b, distinct) inside {1..n}. Its values are OEIS A143824; the brute force and
the CP-SAT model are deliberately written differently.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time

# n -> value, from the literature. Cite the source of every entry.
# Source: OEIS A143824 (size of largest Sidon subset of {1..n}); first terms.
KNOWN: dict[int, int] = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4,
                         11: 4, 12: 5, 13: 5, 14: 5, 15: 5, 16: 5, 17: 5, 18: 6}


def is_sidon(s: tuple[int, ...]) -> bool:
    sums = set()
    for i, a in enumerate(s):
        for b in s[i:]:
            if a + b in sums:
                return False
            sums.add(a + b)
    return True


def compute_bruteforce(n: int) -> int:
    """Implementation A: exhaustive, with the symmetry x -> n+1-x broken by fixing 1 in the set."""
    best = 1
    for k in range(2, n + 1):
        found = False
        # WLOG the set contains 1 (translate down); this is a valid symmetry for Sidon sets.
        for rest in itertools.combinations(range(2, n + 1), k - 1):
            if is_sidon((1,) + rest):
                found = True
                break
        if not found:
            return best
        best = k
    return best


def compute_cpsat(n: int) -> int:
    """Implementation B: CP-SAT model on differences (a Sidon set has all differences distinct)."""
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n + 1)]  # x[i] = i in set
    m.Add(x[0] == 0)
    # each positive difference d occurs at most once
    for d in range(1, n):
        pairs = []
        for i in range(1, n + 1 - d):
            p = m.NewBoolVar(f"p{i}_{d}")
            m.AddBoolAnd([x[i], x[i + d]]).OnlyEnforceIf(p)
            m.AddBoolOr([x[i].Not(), x[i + d].Not()]).OnlyEnforceIf(p.Not())
            pairs.append(p)
        m.Add(sum(pairs) <= 1)
    m.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.num_workers = 8
    s.parameters.max_time_in_seconds = 120
    st = s.Solve(m)
    if st != cp_model.OPTIMAL:
        raise RuntimeError(f"CP-SAT did not prove optimality for n={n} (status {s.StatusName(st)})")
    return int(round(s.ObjectiveValue()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-n", type=int, default=12)
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--json", help="write results here")
    ap.add_argument("--allow-beyond-known", action="store_true",
                    help="continue past the largest known n (only after the known range passes)")
    a = ap.parse_args()

    impls = {"bruteforce": compute_bruteforce, "cpsat": compute_cpsat}
    rows, ok = [], True
    top_known = max(KNOWN)
    for n in range(a.min_n, a.max_n + 1):
        if n > top_known and not a.allow_beyond_known:
            print(f"stop at n={n}: beyond known range; rerun with --allow-beyond-known once all checks pass")
            break
        vals, times = {}, {}
        for name, f in impls.items():
            t = time.perf_counter()
            try:
                vals[name] = f(n)
            except Exception as e:  # a failing implementation is a finding, not a crash
                vals[name] = f"error: {e}"
            times[name] = round(time.perf_counter() - t, 3)
        agree = len({str(v) for v in vals.values()}) == 1
        known = KNOWN.get(n)
        match = known is None or all(v == known for v in vals.values())
        status = "OK" if agree and match else ("NEW?" if agree and known is None else "MISMATCH")
        ok &= status != "MISMATCH"
        rows.append({"n": n, "known": known, **vals, "times": times, "status": status})
        print(f"n={n:3d} known={known!s:>5} " + " ".join(f"{k}={v}" for k, v in vals.items())
              + f"  {status}  {times}")
        if status == "MISMATCH":
            print("  -> stop: debug the checker or the reading of the statement before going further")
            break
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
