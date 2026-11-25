# Solver cookbook

## SAT encodings (PySAT)

```python
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
pool = IDPool()
x = lambda i, c: pool.id(("x", i, c))          # readable variable names
f = CNF()
f.extend(CardEnc.equals([x(i, c) for c in range(k)], 1, vpool=pool, encoding=EncType.seqcounter).clauses)
f.extend(CardEnc.atmost(lits, bound=b, vpool=pool, encoding=EncType.totalizer).clauses)
```

- **At-most-one**: pairwise for ≤ 6 literals, sequential counter or
  commander beyond.
- **Cardinality**: totalizer or sequential counter (`pysat.card`); for
  optimisation use incremental totalizer (`ITotalizer`) and tighten the bound.
- **Solvers**: `cadical195`, `glucose4`, `maplechrono`. For big instances
  dump DIMACS (`f.to_file`) and run `kissat` or `cadical` binaries with proofs.

## Symmetry breaking (each one is a theorem; write its proof in a comment)

- **Value symmetry** (interchangeable colours): element i uses colour < i
  (first-occurrence order). Sound for any problem invariant under permuting
  colours.
- **Translation / reflection** of subsets of [n]: fix the minimum to 1, or
  require x ↦ n+1−x image to be lexicographically ≥.
- **Graph automorphisms**: lex-leader constraints on the adjacency matrix rows
  (Codish et al.), or generate only canonical graphs with `geng`.
- **Static vs dynamic**: BreakID computes symmetry-breaking clauses for a CNF
  automatically; useful to check whether you missed a symmetry.

## UNSAT certificates

```bash
kissat --no-binary f.cnf f.drat ; drat-trim f.cnf f.drat          # DRAT
cadical --lrat f.cnf f.lrat ; cake_lpr f.cnf f.lrat                # LRAT, verified checker
```

Symmetry-breaking clauses added by hand are *not* covered by the DRAT proof:
the proof only shows the CNF with those clauses is UNSAT. Their soundness is
your mathematical argument, and must appear in the write-up (or be verified,
e.g. in Lean).

## CP-SAT (OR-Tools)

```python
from ortools.sat.python import cp_model
m = cp_model.CpModel(); x = [m.NewBoolVar(f"x{i}") for i in range(n)]
m.AddBoolOr([...]); m.Add(sum(x) <= k); m.AddImplication(a, b)
m.Maximize(sum(x))
s = cp_model.CpSolver(); s.parameters.num_workers = 8; s.parameters.max_time_in_seconds = 600
st = s.Solve(m); s.StatusName(st); s.ObjectiveValue(); s.BestObjectiveBound()
```

Only `OPTIMAL` proves the value; `FEASIBLE` gives a lower bound, and
`BestObjectiveBound()` an upper bound. CP-SAT does not emit certificates; for
a publishable optimality claim, confirm with a second solver or produce a SAT
encoding with a DRAT proof for "no solution of size k+1".

## ILP (HiGHS)

`highspy` or `scipy.optimize.milp`. Watch numerics: use integer data, check
the returned solution exactly in Python, and treat the dual bound as
heuristic unless solved to zero gap with exact arithmetic (SCIP-exact,
or re-verify by SAT).

## Z3

```python
from z3 import Int, Ints, Solver, Distinct, And, Or, sat
a, b = Ints("a b"); s = Solver(); s.add(a > 0, b > 0, a*a + b*b == 2*a*b + 1)
s.check() == sat and s.model()
```

Good for: number-theoretic side conditions, bit-vectors, quick sanity checks
of algebraic identities on small domains. Nonlinear integer arithmetic is
undecidable; Z3 may return `unknown`.

## Graphs

- `geng -c n` (nauty) for all connected graphs up to isomorphism; pipe through
  a filter. `nauty` canonical labelling for deduplication.
- House of Graphs for known extremal graphs; `networkx` for prototyping only.
