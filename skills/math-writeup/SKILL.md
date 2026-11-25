---
name: math-writeup
description: Writes up and shares a verified math result or misformalisation finding - a short forum note for the problem's thread with plain AI-use disclosure, a formal-conjectures pull request with the @[formal_proof] attribute and Palomar link, a Zulip post, and when warranted a short human-readable arXiv paper. Use after verify-gate and novelty-check, or when the user wants to report a result, a counterexample, a negative computational result, or a misformalised Lean statement.
license: Apache-2.0
compatibility: Model-only for drafting; posting needs the user's accounts (erdosproblems.com, GitHub, Zulip, arXiv).
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Write-up and sharing

Maintainers' main complaint is long, unread AI-generated papers. Write the
shortest thing that lets an expert check the result in ten minutes.
Draft everything for the user; the user posts under their own name.

Preconditions: `verify-gate` PASS output attached; `novelty-check` verdict
written. If either is missing, the only thing to post is a question.

## 1. Forum note (erdosproblems.com thread or the source's page)

Check the forum's current rules first: there were reports in 2026 of the site
restricting comments because of a flood of AI proofs. Then:

```
Problem N: <proof | counterexample | partial result | reference found>

Result. <one sentence, precise>
Idea. <3–6 sentences: the key idea a human needs>
Verification. Lean 4 proof (Mathlib <rev>, formal-conjectures <tag>): <link to
repo at a fixed commit>. Checked: no sorry, standard axioms only, statement
identical to FormalConjectures/ErdosProblems/N.lean.
Literature. Searched <sources> on <date>; closest: <refs>.
AI use. <Which models/tools did what: e.g. "Claude (model X) proposed the
construction and wrote most of the Lean proof; SAT search with CaDiCaL; I
checked the argument and the statement.">
```

Disclose AI use plainly and specifically. Vague disclosure ("AI-assisted")
is the norm people complain about.

## 2. formal-conjectures pull request

Follow the repo's CONTRIBUTING.md (sign the Google CLA; open an issue first;
human review). For a solved problem:

```lean
@[category research solved, AMS 11]
@[formal_proof using formal_conjectures at "https://palomar-registry.org/entry.html?id=<id>"]
theorem erdos_N : <unchanged statement> := by
  <proof>       -- only if short; otherwise keep `sorry` and link the proof
```

- `using` takes `formal_conjectures` (proof in this repo), `lean4` (elsewhere
  in Lean 4), or `other_system`.
- For research-solved problems the link must be a Palomar entry
  (`https://palomar-registry.org/entry.html?id=…`). Register first: Palomar
  takes a fixed commit hash of a public Lean repo (submission form at
  submit.palomar-registry.org; policy in the PalomarRegistry GitHub org).
- Proofs longer than roughly 25–50 lines belong in an external repo, linked.
- Yes/no `@[question]` statements: follow the repo's convention for stating
  the resolved answer (`P` or `¬ P`).
- Do not include your `Work/` files or change unrelated statements.

For a **misformalisation**: open an issue first with (a) the source statement,
(b) the Lean statement, (c) an explicit witness showing they differ (ideally a
Lean proof that the formal version is trivially true/false), (d) a proposed fix.

## 3. Zulip

Post in the Formal Conjectures channel on leanprover.zulipchat.com: two lines
of result, link to PR and Palomar entry, one line of AI disclosure.

## 4. arXiv (only for a clean, new, human-readable result)

Structure: abstract (3 sentences), introduction with the problem and
history (1 page), the proof (as short as possible, human-readable; generate a
first draft from the Lean proof with the formal-to-informal prompt in
`proof-blueprint/references/prompt-patterns.md`, then rewrite), computational
details if any, a section "Formal verification and use of AI" with links, and
references actually read. Target under 10 pages. Have a mathematician read it
before submission; arXiv endorsement may be required.

## 5. Negative results

A clearly bounded negative result ("no counterexample with n ≤ 40, verified
by SAT with DRAT proofs; encoding validated on known values n ≤ 12") is worth a
forum post. It saves the next person the compute.
