---
name: problem-intake
description: Picks and triages an open problem, copies its formal-conjectures statement verbatim into a locked work file, and audits the formalisation against the source. Use when choosing which Erdős or formal-conjectures problem to attack, when starting work on a specific problem number, or when checking whether a Lean statement faithfully matches the original conjecture (misformalisation hunting).
license: Apache-2.0
compatibility: Needs a built formal-conjectures checkout (see lean-setup) and Python 3.10+.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Problem intake

Output of this phase: a work file that compiles with one `sorry`, a statement
hash, a filled-in triage card, and a misformalisation verdict.

## 1. Pick a problem worth the time

Score candidates on this card before committing. Be honest; the point is to
avoid sinking a week into a problem a lab will solve on Tuesday.

```
problem:            Erdős #___ / FormalConjectures/<Source>/<File>.lean : <name>
category tag:       research open | research solved | ...
type:               finite/decidable | asymptotic | existence/construction | value question
small-case handle:  can a computer test n = 1..k? (yes / partly / no)
literature depth:   obscure (few citations) | studied | famous
race flag:          on FrontierMath: Erdős list? (check epoch.ai) yes/no
AI history:         prior AI attempts recorded? (tracker, forum)
definitions:        all in Mathlib | uses FormalConjecturesForMathlib | bespoke in file
gut difficulty:     1 (exercise once found) .. 5 (needs new idea)
```

Prefer: obscure, finite or computable handle, definitions already in Mathlib,
not on the FrontierMath list. Famous problems are open because they are hard.
Obscure ones are often open because nobody looked, which is where tools win.

Find candidates:

```bash
grep -rl "category research open" FormalConjectures/ErdosProblems | head
python3 scripts/statement_tools.py list FormalConjectures/ErdosProblems/123.lean
```

## 2. Lock the statement

```bash
python3 scripts/statement_tools.py extract FormalConjectures/ErdosProblems/123.lean erdos_123
python3 scripts/statement_tools.py scaffold FormalConjectures/ErdosProblems/123.lean erdos_123 \
    --root . --out Work/Erdos123/Main.lean
lake env lean Work/Erdos123/Main.lean      # expect exactly one "declaration uses 'sorry'"
```

`scaffold` imports the problem file (so bespoke definitions come along),
restates the theorem verbatim under a new name, and writes
`Main.lock.json` with the original name and the statement hash. From here on:

- **Never edit the statement.** Not to fix a typo, not to "clarify" a type,
  not to add a hypothesis you think is implied. If the statement is wrong,
  that is a finding (section 3), not something to patch silently.
- Never reference the original declaration in your proof: it is `sorry`.
- If the problem file has solved variants (`@[category research solved]`),
  read their proofs. They show the house style, the useful API, and often a
  special case of the technique you need.

## 3. Audit the formalisation (do this every time)

Read the docstring, the `*Reference:*` link, and the source page side by side
with the Lean. Formalisations go wrong in predictable ways; check each item in
`references/misformalisation-checklist.md`. The fast version:

- Off-by-one and boundary: `<` vs `≤`, `ℕ` including 0, `Finset.range n` is
  `{0,…,n-1}`, `Icc` vs `Ico`.
- Truncated arithmetic: `ℕ` subtraction and division silently truncate; `/` on
  `ℕ` is floor; `(a - b : ℕ)` is 0 when `b > a`.
- Junk values: `1/0 = 0`, `Real.log 0 = 0`, `sSup ∅ = 0`, `Nat.find` needs a
  proof; a statement can become trivially true through junk.
- Quantifier order and "sufficiently large": `∀ ε > 0, ∃ N, ∀ n ≥ N` vs
  `∃ N, ∀ ε` — easy to swap; asymptotics with `=o[atTop]` vs `≪`.
- Vacuity: are the hypotheses satisfiable? Try to instantiate them in Lean
  (`example : ∃ x, hyp x := ⟨_, by decide⟩`). An unsatisfiable hypothesis makes
  the theorem trivially true.
- Triviality: does `simp`, `decide`, `omega` or `exact?` close it? If a
  "research open" statement falls to `simp`, it is misformalised.
- Disproving the formal version cheaply: if a small counterexample exists to
  the Lean statement but not to the source statement, the formalisation is wrong.

Quick automated probes, from the project root, on the work file:

```lean
example : <statement> := by simp      -- should fail
example : <statement> := by decide    -- should fail (or time out)
example : ¬ <statement> := by simp    -- should fail
```

If you find a misformalisation, stop and write it up (`math-writeup`, section
"misformalisation report"). It is a real contribution and the maintainers want
it; it also means any proof of the current statement is worthless.

## 4. Record

Append to `Work/<ProblemId>/NOTES.md`: triage card, hash, audit verdict
(faithful / suspicious: why / misformalised: counterexample), and the source
links. Then move to `small-cases`.
