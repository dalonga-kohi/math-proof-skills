# From a found object to a Lean proof

An explicit finite counterexample usually gives a short Lean proof: exhibit
the object, then let the kernel check the property by computation.

## Shape

```lean
-- Statement (from the locked work file):  theorem foo : ∀ n, P n
-- Disproof: the theorem is false, so prove its negation.
theorem foo_false : ¬ ∀ n, P n := by
  intro h
  have := h 13           -- the counterexample parameter
  revert this
  decide                 -- kernel evaluates ¬ P 13
```

For formal-conjectures `@[question]` problems the file states either `P` or
`¬ P`; prove whichever the resolved answer is, without editing the statement
form agreed in the repo (see the repo's PROOFS.md / STATEMENTS.md).

## Witness encodings that `decide` handles well

- Colourings: `def c : Fin 13 → Fin 3 := ![0,1,1,0,2,2,2,2,2,0,1,1,0]`.
- Sets: `Finset` literals `({1, 2, 4, 8} : Finset ℕ)`; quantify with
  `∀ a ∈ S, ∀ b ∈ S, …` — `Finset` membership is decidable.
- Graphs: adjacency as `Fin n → Fin n → Bool` from a bit table, then a
  `SimpleGraph.fromRel` wrapper; prove properties about the `Bool` version and
  transfer with a small lemma.
- Bounded quantifiers over `ℕ`: rewrite `∀ x < N` as `∀ x : Fin N` or use
  `Nat.decEq`/`Nat.forall_lt_succ`-style lemmas so `decide` sees a finite domain.

## Choosing the decision tactic

| Tactic | Trust | Speed | Notes |
|---|---|---|---|
| `decide` | kernel only | slowest | default; may need `set_option maxRecDepth` |
| `decide +kernel` | kernel only | faster (skips elaborator evaluation) | Lean ≥ 4.12 syntax; check it exists on the pinned toolchain |
| `simp` / `norm_num [Finset.sum_range_succ]` | kernel | good for arithmetic facts | |
| `native_decide` | trusts the compiler (adds axiom `Lean.ofReduceBool`) | fastest | **avoid for results you will publish**; Mathlib disallows it, and reviewers / Palomar's checks may reject it. Use to explore, then replace |

If `decide` is too slow: (1) shrink the witness; (2) make the checking
function structurally recursive on `Nat`/`List` (kernel reduction hates
well-founded recursion); (3) split the check into lemmas over sub-ranges;
(4) prove the property via a verified checker (write the checker in Lean,
prove it sound once, run it with `decide` on the data).

## UNSAT results in Lean

A SAT-solver UNSAT proof is not a Lean proof. Options, cheapest first:

1. If the instance is small, `decide` directly on the Lean statement.
2. Verified pipeline: LRAT proof checked by a Lean-verified checker
   (Lean's `bv_decide` uses LRAT internally for bit-vector goals; for custom
   encodings, the Heule–Scheucher empty-hexagon formalisation is the model:
   prove the encoding correct in Lean, check the LRAT certificate).
3. Otherwise present it as a computer-assisted result with a checked DRAT/LRAT
   certificate, and be explicit that Lean did not check it.

## Always

- Run `verify-gate` on the final file.
- Keep the witness in the repo as data (JSON) with a script that regenerates
  the Lean literal, so reviewers can reproduce it.
