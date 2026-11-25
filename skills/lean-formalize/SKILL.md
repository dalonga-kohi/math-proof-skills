---
name: lean-formalize
description: Formalises a proof blueprint in Lean 4 with Mathlib lemma by lemma, compiling after every step through the lean-lsp MCP tools (live goals, diagnostics, LeanSearch, Loogle, multi-attempt). Use when writing or repairing Lean proofs, when a Lean goal or error needs to be resolved, when searching Mathlib for a lemma, or when turning an informal argument or counterexample into checked Lean code.
license: Apache-2.0
compatibility: Needs a built Lean 4 + Mathlib project (formal-conjectures recommended) and ideally the lean-lsp MCP server; falls back to `lake env lean`.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Lean formalisation

## The loop (never skip the compile)

1. **Skeleton first.** Write every blueprint lemma as a `lemma … := by sorry`
   and the main theorem's proof using them. Compile. The skeleton must
   type-check before any lemma is proved: this catches mis-stated lemmas
   (wrong types, missing hypotheses) at the cheapest moment.
2. **One lemma at a time**, leaves first. For each:
   - `lean_goal` at the `sorry` to see the exact goal.
   - Search before you write: `lean_leansearch` (natural language),
     `lean_loogle` (type pattern, e.g. `Finset.card (Finset.filter _ _) ≤ _`),
     `lean_leanfinder`, `lean_local_search` (ripgrep, no rate limit).
   - Try the tactic ladder (below) with `lean_multi_attempt` before writing
     long manual proofs.
   - Edit, then `lean_diagnostic_messages`. Fix the first error only; later
     errors are often consequences.
3. **Commit progress** (`git commit` in your work dir) whenever the sorry count
   drops. Lean files that once compiled are your checkpoints.
4. Without MCP: `lake env lean Work/<Id>/Main.lean` after every edit.

## Tactic ladder (try in roughly this order)

`rfl`, `simp`, `simp?` (then replace with the `simp only` it prints),
`omega` (linear ℕ/ℤ arithmetic), `decide` (finite, decidable),
`norm_num`, `positivity`, `linarith` / `nlinarith [sq_nonneg (a - b)]`,
`ring` / `ring_nf`, `field_simp`, `gcongr`, `aesop`, `grind` (if available on
the pinned toolchain), `exact?`, `apply?`, `rw?`, `hint`. Use
`lean_hammer_premise` for premise suggestions on stubborn goals.

## House rules (violations are caught by verify-gate)

- The locked statement is not edited, renamed hypotheses included.
- No `axiom`, `sorry`, `admit`, `native_decide` in the final proof (see
  `references/lean-pitfalls.md` for why `native_decide` is excluded).
- No `set_option` that weakens checking (`debug.skipKernelTC`, etc.).
  `maxHeartbeats` and `maxRecDepth` increases are fine but note them.
- No `@[implemented_by]`, `@[extern]`, `unsafe`, or custom `macro`/`elab`
  that could hide a proof.
- Never use the original problem theorem (it is `sorry`).

## Mathlib search discipline

- LLMs hallucinate Mathlib names. Never use a name you have not seen in a
  search result or in `lean_hover_info`. If `exact Foo.bar` fails with
  "unknown identifier", search; do not guess variants.
- Mathlib naming conventions help guess search terms:
  `Finset.card_le_card`, `Nat.Prime.two_le`, `mul_le_mul_of_nonneg_left` —
  conclusion first, `_of_` before hypotheses.
- Hosted search tools allow 3 requests / 30 s each. Batch your questions;
  prefer `lean_local_search` for name lookups.

## When stuck (> 3 failed attempts on one goal)

1. Is the goal true? Test it numerically. False goals come from a mis-stated
   lemma or a lost hypothesis upstream; fix upstream.
2. Generalise or specialise: `induction` needs the right generalisation
   (`induction n generalizing m`); a goal with a concrete number may be
   `decide`-able.
3. Change representation: `Finset` ↔ `Set` ↔ `List`, `ℕ` ↔ `ℤ` (`push_cast`,
   `zify`, `qify`), `Fin n` ↔ `ℕ` with bound.
4. Split off the goal as a standalone lemma and send it to `auto-prover`.
5. Go back to `proof-blueprint` with the exact goal (stuck-recovery prompt).

## References

- `references/lean-pitfalls.md` — ℕ subtraction, coercions, `decide` limits,
  `native_decide` trust, universe and instance issues, performance.
