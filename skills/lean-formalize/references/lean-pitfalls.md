# Lean 4 / Mathlib pitfalls for research formalisation

## Arithmetic
- `ℕ` subtraction truncates: `(3 - 5 : ℕ) = 0`. Before `omega` can help,
  you may need `Nat.sub_add_cancel h`. Prefer moving to `ℤ` (`zify [h]`) when
  subtraction is essential.
- `ℕ`/`ℤ` division floors; `Int.ediv` vs `Int.div` vs `Int.tdiv` round
  differently on negatives (names have changed across versions; hover).
- Casts: `push_cast`, `norm_cast`, `exact_mod_cast`, `Nat.cast_le`. A goal
  that "should" be `linarith` often fails because one side has `↑(a - b)`.
- Real powers: `x ^ (n : ℕ)` (Monoid.npow) vs `x ^ (y : ℝ)` (rpow) are
  different functions with different lemma families.

## Decidability and computation
- `decide` evaluates in the kernel; it fails on well-founded recursion and on
  instances implemented via `Classical`. Use structural recursion, `Fin`,
  `List.range`, `Finset.range`.
- `native_decide` compiles to native code and trusts the compiler: the proof
  depends on the axiom `Lean.ofReduceBool` and is only as trustworthy as the
  code generator and every `@[implemented_by]` in scope. Mathlib forbids it.
  Explore with it, publish without it.
- `Nat.find`, `Classical.choice`, `sSup` are not computable: statements using
  them cannot be `decide`d directly; prove an equivalence to a computable form.

## Elaboration and statements
- Implicit vs explicit binders and instance arguments can make two
  "identical-looking" statements different. The verify-gate `type_of%` check
  compares elaborated types, not text.
- `open … in` and local notation in the original file affect how the statement
  elaborates; the scaffold copies top-level `open`/notation lines, but check.
- formal-conjectures files use Lean's module system (`module`, `public import`,
  `@[expose] public section`). If an import of a problem file fails or a
  definition looks opaque, check whether it is exported publicly.
- Universe polymorphism: copying a statement with `Type*` into a context with
  a fixed universe can change it. Do not "simplify" universes.

## Performance
- `simp` without `only` on a large goal can time out; use `simp?` once, then
  `simp only [...]`.
- `decide` on large finite structures: raise `maxRecDepth`, or prove via a
  verified checker function.
- `set_option maxHeartbeats 400000 in` for one declaration is acceptable;
  needing 10× that usually means a bad proof strategy.
- `lean_profile_proof` (lean-lsp-mcp) shows slow lines.

## Proof engineering
- State lemmas at the right generality: too specific blocks induction, too
  general blocks automation.
- Name hypotheses; avoid `this` chains longer than two.
- Keep each lemma under ~50 lines. formal-conjectures asks that proofs longer
  than roughly 25–50 lines live in an external repo and be linked.
