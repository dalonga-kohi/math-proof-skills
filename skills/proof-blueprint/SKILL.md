---
name: proof-blueprint
description: Turns a conjecture into an informal proof blueprint - a prose argument broken into a dependency graph of small, precisely stated lemmas, each tagged with how it will be proved in Lean - and red-teams it before any formalisation. Use when reasoning toward a proof of an open problem, when the user asks for a proof sketch, strategy, or approach, when a Lean attempt is stuck and needs a new mathematical idea, or to review an LLM-generated proof for gaps.
license: Apache-2.0
compatibility: Model-only skill; no tools required. Pairs with lean-formalize and math-swarm.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Proof blueprint

Prose first, Lean second. But prose written for Lean: every step must be a
statement precise enough that a stranger could formalise it without asking
you what you meant.

## 1. Understand before attacking (write these down)

1. Restate the problem in your own words, then translate back to the Lean
   statement and check they match.
2. Why is it plausible? What do the small cases (phase 2) show: extremal
   examples, structure, where the bound is tight?
3. What is the obvious approach, and why hasn't it worked? Look for the
   obstruction. If you cannot name one, you probably have not understood why
   the problem is open — or it is open only because nobody tried (common).
4. Which known theorems are nearby? Mathlib names if possible
   (`lean_leansearch`, `lean_loogle`).
5. Special cases and variants: prove a weaker version first (smaller range,
   extra hypothesis, worse constant). Solved variants in the problem file are
   hints about which special cases are tractable.

## 2. Generate several strategies, not one

Produce 3–5 genuinely different approaches before developing any, for example:
induction / minimal counterexample; extremal or probabilistic method;
algebraic (polynomial method, characters, linear algebra bounds); analytic
(generating functions, density increment); reduction to a known theorem;
compactness or finite-to-infinite transfer; explicit construction. For each:
one paragraph, the key lemma it needs, and the step most likely to fail.

## 3. Blueprint format

```markdown
## Theorem (locked)  <Lean name>, sha256 <hash>
## Strategy  <one paragraph>
## Lemmas (dependency order)
L1. <precise statement, with all quantifiers and types>
    depends on: —        Mathlib: <names or "none found">
    proof idea: <2–5 lines>
    Lean plan: <tactics/library, e.g. "Finset.card_le_card + omega">
    risk: low | medium | high   (why)
L2. ...
## Main proof from lemmas  <how L1..Ln combine; should be short>
## Known weak points
```

Rules for the lemma list:

- Each lemma small enough to formalise in under ~50 lines; split otherwise.
- No "clearly", "it is easy to see", "by a standard argument". Those are
  where wrong LLM proofs hide. Replace each with a lemma or a citation.
- Track all edge cases explicitly (n = 0, empty set, equality cases).
- Mark which lemmas are routine (send to `auto-prover`) and which carry the
  idea (keep for careful work).

## 4. Red-team before formalising

Formalisation is expensive; finding a gap now is cheap. Ask a *different*
agent or model (ideally) to act as referee with this brief:

> You are a hostile referee. The following is claimed to prove an open
> problem, which makes it very likely wrong. Find the first step that does not
> follow. Check every quantifier, every edge case, every use of a cited
> theorem's hypotheses. Test each lemma on the small cases in the attached
> table. If you find no error, say which step you are least sure of and why.

Then test every lemma numerically on small cases yourself. A lemma that fails
for n = 7 kills the approach in seconds; Lean would take an hour to tell you.

Signs the argument is wrong: it never uses a hypothesis; it would also prove
a known-false variant (try removing a hypothesis or changing a constant);
it gives a bound better than a known lower-bound construction; it is short
and elementary for a problem that experts have studied for decades.

## 5. Hand-off

Save as `Work/<Id>/BLUEPRINT.md`. Next: `lean-formalize`, starting with the
main proof assembled from lemma stubs (`sorry`) so the skeleton type-checks
before any lemma is proved.

`references/prompt-patterns.md` has prompts for strategy generation,
lemma-splitting, referee, and "stuck" recovery.
