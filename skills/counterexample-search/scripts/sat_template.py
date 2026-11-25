#!/usr/bin/env python3
"""SAT template: k-colourings of {1..n} with no monochromatic x + y = z (Schur numbers).

Known values (Schur numbers S(k) = largest n with a valid k-colouring):
  S(1)=1, S(2)=4, S(3)=13, S(4)=44 (Baumert 1965), S(5)=160 (Heule 2017, SAT + DRAT proof).
This script reproduces S(2) and S(3) in seconds, and writes:
  - the witness colouring for n = S(k) as JSON (to become a Lean `decide` proof), and
  - a DIMACS CNF for n = S(k)+1 that you can re-solve with kissat/cadical and
    certify with a DRAT/LRAT proof checker (e.g. drat-trim, cake_lpr).

Adapt: replace `encode()` for your problem. Keep the symmetry-breaking clauses
separate and documented, because each one is a mathematical claim.

    python3 sat_template.py --k 3 --out Work/Schur
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pysat.formula import CNF
from pysat.solvers import Solver


def var(i: int, c: int, k: int) -> int:
    """DIMACS variable for 'element i (1-based) has colour c (0-based)'."""
    return (i - 1) * k + c + 1


def encode(n: int, k: int, symmetry: bool = True) -> CNF:
    f = CNF()
    for i in range(1, n + 1):
        f.append([var(i, c, k) for c in range(k)])                 # at least one colour
        for c in range(k):                                         # at most one colour
            for d in range(c + 1, k):
                f.append([-var(i, c, k), -var(i, d, k)])
    for x in range(1, n + 1):                                      # no monochromatic x + y = z
        for y in range(x, n + 1 - x):
            z = x + y
            for c in range(k):
                f.append([-var(x, c, k), -var(y, c, k), -var(z, c, k)])
    if symmetry:
        # Colours are interchangeable: WLOG element 1 has colour 0, and colour c is used
        # for the first time no earlier than colour c-1 (value-symmetry breaking via
        # "first occurrence" ordering, the simple version: element i has colour < i).
        f.append([var(1, 0, k)])
        for i in range(1, n + 1):
            for c in range(i, k):
                f.append([-var(i, c, k)])
    return f


def solve(n: int, k: int, solver: str = "cadical195") -> list[int] | None:
    with Solver(name=solver, bootstrap_with=encode(n, k).clauses) as s:
        if not s.solve():
            return None
        model = set(l for l in s.get_model() if l > 0)
        return [next(c for c in range(k) if var(i, c, k) in model) for i in range(1, n + 1)]


def check(col: list[int]) -> bool:
    """Independent checker, no SAT involved."""
    n = len(col)
    return all(not (col[x - 1] == col[y - 1] == col[x + y - 1])
               for x in range(1, n + 1) for y in range(x, n + 1 - x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--stop", type=int, default=200)
    ap.add_argument("--out", default="schur_out")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    last = None
    for n in range(a.start, a.stop + 1):
        col = solve(n, a.k)
        if col is None:
            print(f"k={a.k}: UNSAT at n={n}  =>  S({a.k}) = {n-1} (given symmetry breaking is sound)")
            encode(n, a.k).to_file(str(out / f"schur_k{a.k}_n{n}.cnf"))
            break
        assert check(col), "SAT model fails the independent checker: encoding bug"
        last = col
    if last:
        (out / f"schur_k{a.k}_n{len(last)}_witness.json").write_text(json.dumps(last))
        print(f"witness for n={len(last)} written; colours: {''.join(map(str, last))}")


if __name__ == "__main__":
    main()
