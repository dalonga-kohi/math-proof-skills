---
name: small-cases
description: Reproduces the known small cases of a conjecture in code with two independent checkers before any new search, and cross-checks the Lean statement's meaning against the source's. Use right after picking a problem, before searching for counterexamples or trusting any computation, when a computed value disagrees with the literature, or when the user asks to "check small n", "compute the first values" or "test the conjecture numerically".
license: Apache-2.0
compatibility: Python 3.10+. Optional solvers - python-sat, ortools, z3-solver, highspy.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Small cases

The purpose is not the numbers. It is to debug three things at once: your
reading of the statement, your checker, and the formalisation. Any search you
run later is only as trustworthy as the checker that passed this phase.

## Protocol

1. **Collect the known values with sources.** The problem page, the original
   paper, OEIS (search the first few terms you expect), survey tables. Write
   each value with its citation into `KNOWN` in `scripts/harness.py`. Values
   without a source are hypotheses, not test data.
2. **Write two independent implementations.** Different algorithms, ideally
   different authors (a second agent, or a solver model vs a brute force).
   The shipped harness pairs exhaustive enumeration with a CP-SAT model.
   Sharing a helper function between the two defeats the purpose.
3. **Compute the Lean meaning too.** Where the Lean statement can be evaluated
   (`decide`, `#eval` on a computable version), evaluate it for small n and
   compare with the source's values. Disagreement means misformalisation or
   misreading; go back to `problem-intake`.
4. **Run the harness on the known range.** It stops at the first mismatch and
   refuses to go beyond the known range until everything agrees.
5. **Only then extend.** `--allow-beyond-known` lets it continue. New values
   are "NEW?" until a second method or a certificate confirms them.

```bash
python3 scripts/harness.py --max-n 18 --json Work/<Id>/small_cases.json
```

## Making brute force fast enough

- **Symmetry breaking** is where orders of magnitude come from. Fix what you
  can WLOG: colour of element 1, the minimum element of a translation-invariant
  set, a vertex of maximum degree, lexicographically smallest representative
  under the automorphism group. State each WLOG in a comment and justify it;
  a wrong WLOG silently loses counterexamples.
- **Canonical augmentation** (McKay) or `nauty`/`geng` for graphs: never
  enumerate labelled graphs above ~8 vertices. `geng -c 10` lists connected
  graphs on 10 vertices up to isomorphism.
- **Incremental checks**: test the forbidden pattern only on configurations
  that include the newly added element.
- **Use the literature's data**: House of Graphs, OEIS b-files, Brendan McKay's
  combinatorial data pages, Gordon Royle's tables. Cross-check against them.

## Red flags

- Your value matches the literature for all n except one: usually an
  off-by-one in the range, or the literature uses a different convention
  (0-indexed, inclusive bound, labelled vs unlabelled).
- Both implementations agree with each other but not with the literature:
  shared misreading of the statement. Re-read the source.
- Floating point anywhere in an exact problem: use `fractions.Fraction`,
  integers, or exact rationals in the solver.

## Hand-off

Record in `NOTES.md`: the table, sources, commands, run times, and the
largest n checked by each method. That last number is the baseline any
"new" search must beat. Next: `counterexample-search` or `proof-blueprint`.
