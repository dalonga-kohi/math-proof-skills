# Misformalisation checklist

Work through every item. For each, write "ok", "n/a" or what you found.
A misformalisation found is worth reporting even if you never prove anything.

## Domain and types
- [ ] Natural numbers: does the source include 0? Lean's `ℕ` does. `n > 0`
      hypotheses missing?
- [ ] Integers vs naturals vs reals: is a bound stated over `ℕ` where the
      source means real `x`? (`∀ x : ℝ, x ≥ 1` vs `∀ n : ℕ`)
- [ ] Coercions: where does `↑` happen? `((a - b : ℕ) : ℝ)` differs from
      `(a : ℝ) - b`. Hover each coercion.
- [ ] Division: `ℕ` and `ℤ` division floor; `Int.div` vs `Int.ediv` rounding.
- [ ] Finite vs infinite sets: `Set` vs `Finset`; `Set.Infinite` vs
      "arbitrarily large"; `ncard` of an infinite set is 0.

## Intervals and ranges
- [ ] `Finset.range n = {0, …, n-1}`; `Finset.Icc 1 n = {1, …, n}`.
- [ ] Open/closed ends: `Ioo`, `Ico`, `Ioc`, `Icc`.
- [ ] Primes: `Nat.Prime` vs `Prime`; `Nat.primesBelow n` is `< n`.

## Junk values
- [ ] Any `/`, `log`, `sqrt`, `sSup`, `sInf`, `iSup`, `⨆`, `deriv`, `limUnder`,
      `Nat.find`, `Classical.choose` in the statement? Check what happens when
      the argument is outside the intended domain. A statement can be true
      for junk reasons (e.g. `sSup` of an unbounded set of reals is 0).
- [ ] `Filter.Tendsto` to `atTop` vs to a value; `limsup` on unbounded
      sequences.

## Quantifiers and logic
- [ ] Order of `∀ ∃` matches the source exactly.
- [ ] "For all sufficiently large n" = `∀ᶠ n in atTop`; "infinitely many" =
      `∃ᶠ n in atTop` or `Set.Infinite {n | …}`.
- [ ] Asymptotic notation: `=O[atTop]`, `=o[atTop]`, `~[atTop]`; constants
      depend on what? (`∃ C, ∀ n` vs `∀ n, ∃ C` — the latter is trivial.)
- [ ] Yes/no questions: `@[question]` statements state `P` or `¬ P` after
      resolution — which way does the file currently state it?
- [ ] Value questions: `@[question value]` with `def <thm>.answer : T := sorry`
      — the answer is a placeholder; proving needs the real value.

## Satisfiability and triviality
- [ ] Hypotheses satisfiable? Instantiate them.
- [ ] Conclusion not trivially implied (`simp`, `decide`, `omega`, `aesop`,
      `exact?`)?
- [ ] Negation not trivially provable either.
- [ ] Small cases agree with the source's stated small cases (see
      `small-cases`): compute both the Lean-meaning and source-meaning values.

## Source fidelity
- [ ] Read the original source (paper, erdosproblems.com page), not just the
      docstring. Erdős often stated several versions; which one is this?
- [ ] Has the problem been modified on the site since formalisation? Compare
      dates; check the site's changelog/forum.
- [ ] Are there comments on the formal-conjectures issue/PR for this file
      flagging problems?

## Verdict
faithful | suspicious (list) | misformalised (explicit witness)
