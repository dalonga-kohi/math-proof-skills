---
name: counterexample-search
description: Searches for counterexamples and extremal constructions with code - brute force with symmetry breaking, SAT/SMT (CaDiCaL, kissat, Z3, PySAT), ILP/CP-SAT (OR-Tools, HiGHS), and LLM-guided program search in the AlphaEvolve/FunSearch style - then turns a found object into a Lean proof by decide. Use before trying to prove a conjecture, when the user asks to disprove, falsify, find a counterexample, find a construction, improve a bound, or search colourings, designs, graphs or extremal sets.
license: Apache-2.0
compatibility: Python 3.10+. pip install python-sat ortools z3-solver highspy. Optional - kissat/cadical binaries, drat-trim or cake_lpr, nauty, the claude CLI for program search.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Counterexample search

Precondition: `small-cases` passed. Your checker reproduces every known value.
If it does not, stop; a search with an untested checker produces noise.

## Pick the tool by problem shape

| Shape | Tool | Why |
|---|---|---|
| tiny n, rich symmetry | brute force + canonical forms (`nauty`/`geng`) | simplest, easiest to trust |
| colourings, Ramsey/Schur/vdW-type, designs, "no forbidden pattern" | SAT (CaDiCaL, kissat via PySAT or DIMACS) | best engines for pure combinatorial feasibility; UNSAT comes with a DRAT/LRAT certificate |
| arithmetic constraints, mixed integer/real, bit-vectors | SMT (Z3) | theories built in; slower than SAT on pure combinatorics |
| extremal set problems, max/min size, packing/covering | ILP or CP-SAT (OR-Tools CP-SAT, HiGHS) | proves optimality bounds, not just feasibility |
| constructions for large n, asymptotic bounds, "find a better example" | LLM-guided program search (`scripts/evolve.py`) | searches over programs that generate objects, which generalise across n |
| continuous extremal constants | local optimisation (scipy, basin hopping) then exact rationalisation | find numerically, certify exactly |

## SAT workflow (finite statements)

`scripts/sat_template.py` is a worked example (Schur numbers; reproduces
S(2)=4 and S(3)=13 and writes witnesses and the UNSAT CNF). The pattern:

1. Encode; keep **symmetry-breaking clauses separate**, each with a written
   justification. A wrong WLOG makes UNSAT meaningless.
2. Check every SAT model with an independent, solver-free checker (the
   template asserts this).
3. For UNSAT claims, run a standalone solver with proof output
   (`kissat --no-binary cnf proof.drat`, or `cadical cnf proof.drat`) and
   check the proof (`drat-trim cnf proof.drat`, or LRAT with `cake_lpr`).
   A solver saying UNSAT without a checked proof is a claim, not a result.
4. Validate the encoding by reproducing known values (done in phase 2) and,
   for publication, by formally verifying the encoding (Heule–Scheucher's
   empty-hexagon work verified the encoding in Lean).
5. Cube-and-conquer (march_cu + parallel CDCL) for hard instances.

## Program search (constructions)

`scripts/evolve.py` is a small AlphaEvolve-style loop: an LLM rewrites a
program that outputs a construction; a trusted evaluator scores it in a
separate process. Example in `scripts/examples/sidon/` — with the `claude`
backend and Haiku it improved greedy's 27 to a valid 35-element Sidon set in
{1..1000} in two generations.

```bash
python3 scripts/evolve.py --dir scripts/examples/sidon --backend claude --model sonnet --generations 30
python3 scripts/evolve.py --dir my_problem --backend openai --base-url http://localhost:8000/v1 --model <served-model>
```

Rules that make this work:

- The evaluator is the ground truth. Keep it short enough to audit, and
  never let generated code import or modify it. The LLM's task description
  can be wrong; the evaluator cannot be (the example's original task text
  understated the maximum, and the search beat it).
- Search over **programs that build objects**, not objects. A program that
  builds good examples for n = 50 often reveals a family for all n.
- Show the model the top few programs with scores; ask for a different idea,
  not a tweak. Diversity beats greed.
- Score partial progress smoothly (e.g. number of violated constraints) so the
  search has a gradient; reject invalid outputs outright.

## When you find something

1. Re-check the object with a second, independent checker.
2. Shrink it: smallest counterexample, fewest elements, simplest numbers.
   Smaller objects mean cheaper Lean proofs and more convincing papers.
3. Turn it into Lean: see `references/certificate-to-lean.md`. Most explicit
   finite counterexamples become a short proof by `decide`.
4. Re-read the statement. Most "counterexamples" to open problems are
   counterexamples to a misreading. If it breaks the Lean statement but not
   the source statement, you have found a misformalisation.
5. Novelty check before telling anyone (`novelty-check`).

## When you find nothing

Report the searched space precisely: parameters, encoding, symmetry breaking,
solver, time, and the known-value cross-check. "No counterexample for n ≤ 40,
UNSAT certified by DRAT for n = 41..44" is a reusable result.

## References

- `references/solver-cookbook.md` — encodings (cardinality, at-most-one,
  symmetry breaking, lex-leader), CP-SAT/HiGHS patterns, Z3 idioms.
- `references/certificate-to-lean.md` — from witness to Lean proof.
