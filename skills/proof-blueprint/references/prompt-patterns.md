# Prompt patterns for mathematical reasoning with LLMs

Each prompt is a template. Fill the `<…>` slots; keep the constraints.
They are written to counter the specific failure modes of LLMs on hard math:
premature confidence, hand-waving at the crux, silently weakening the claim,
and anchoring on the first idea.

## Strategy generation (diversity)

```
Problem (Lean, locked): <statement>
Informal reading: <restatement>
Small-case data: <table and extremal examples>
Known nearby results: <list>

Propose 5 approaches that differ in their main idea (not variations of one).
For each: (a) the key lemma, stated precisely; (b) why it could work given the
data; (c) the single step most likely to fail and a quick test that would
reveal it. Do not develop any approach fully. Rank by (probability of
success) × (cheapness of the falsification test).
```

## Assigned-angle strategist (for swarms)

```
You are assigned ONE angle: <e.g. "polynomial method">. Other agents cover
other angles; do not drift to theirs. Either produce a blueprint in the
standard format using this angle, or produce a precise obstruction: a reason
this angle cannot work (e.g. "the method gives at most n^{1/2} but the small
cases show the truth is n^{1/2+c}"). An obstruction is a successful outcome.
```

## Lemma splitting

```
Here is a step that is too large to formalise directly: <step>.
Split it into lemmas each provable in ≤ 30 lines of Lean with Mathlib.
For each lemma give the exact statement with types (ℕ/ℤ/ℝ, Finset vs Set),
the Mathlib lemmas you expect to use (names you are unsure of: say so), and
the edge cases (0, empty, equality).
```

## Hostile referee

```
The argument below claims to <prove/disprove> <open problem>. Prior
probability that it is correct is low. Your job is to find the first error.
Check: each quantifier; hypotheses of every cited theorem; edge cases;
whether any step uses something equivalent to the conclusion; whether the
argument proves a known-false variant if you drop <hypothesis>. Evaluate
each lemma on these small cases: <table>. Report: FIRST ERROR (step, why,
counterexample if any) or NO ERROR FOUND + the weakest step.
```

## Stuck recovery (when a Lean goal will not close)

```
Lean goal (verbatim): <goal from lean_goal>
What I tried and the errors: <list>
Is this goal actually true? Test it on small values first. If it is false,
say which earlier step produced a false intermediate claim. If it is true,
give a mathematical reason in two sentences, then the Mathlib lemma names
(verify with search before using), then a tactic proof.
```

## Formal-to-informal rewrite (for the write-up)

```
Here is a complete Lean proof that compiles: <file>. Write a human-readable
proof for a research mathematician: definitions, the key idea first, then
the lemmas in logical order. Do not add any claim that is not in the Lean
proof. Mark every place where the Lean proof uses a computation (decide).
Length: as short as clarity allows.
```

## Anti-patterns to forbid in every prompt

- "Prove that…" with no permission to conclude it is false — models will
  then produce a fake proof. Always allow "this is false / I cannot".
- Asking for the whole proof in one shot for anything non-trivial.
- Letting the model restate the theorem in its own words and then prove the
  restatement. Always paste the locked statement.
