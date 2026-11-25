---
name: math-proof-workflow
description: Entry point and router for proving or disproving open math problems and conjectures with LLMs and Lean 4. Runs the loop pick a problem, reproduce known small cases in code, search or reason for the new case, make Lean check it, check novelty, write up. Use when the user wants to attack an Erdős problem, a formal-conjectures statement, an OEIS or MathOverflow conjecture, or asks "how do I prove/disprove X with AI", and to decide which math-proof skill to load next.
license: Apache-2.0
compatibility: Designed for Claude Code with the lean-lsp MCP server; works in any Agent Skills client that can run shell commands. Needs Lean 4 via elan and Python 3.10+.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Math proof workflow (router)

You are running a research loop whose only acceptable output is a result that
Lean has checked against an untouched statement and that a literature search
has not already found. Everything else is a draft.

## The loop

| Phase | Goal | Skill to load | Exit gate |
|---|---|---|---|
| 0. Setup | Lean + Mathlib + formal-conjectures build; lean-lsp MCP live | `lean-setup` | `doctor.sh` all green |
| 1. Intake | Choose problem, copy statement verbatim, audit formalisation | `problem-intake` | work file compiles with `sorry`; statement hash recorded |
| 2. Small cases | Reproduce every known value in code with two independent checkers | `small-cases` | all known values match; checkers agree |
| 3a. Disprove | Hunt counterexamples (brute force, SAT/SMT, ILP, program search) | `counterexample-search` | explicit object + independent re-check |
| 3b. Prove | Prose blueprint, lemma DAG, red-team it | `proof-blueprint` | every lemma stated; referee found no gap |
| 4. Formalise | Lemma by lemma in Lean, compile after every step | `lean-formalize`, `auto-prover` | zero `sorry` |
| 5. Gate | Statement lock, axioms, forbidden constructs | `verify-gate` | `verify_gate.py` exits 0 |
| 6. Novelty | Same-day literature + tracker + PR check | `novelty-check` | written search log, no prior result |
| 7. Share | Forum note, formal-conjectures PR, Zulip, maybe arXiv | `math-writeup` | AI use disclosed |

For more than one line of attack at once, load `math-swarm`: it runs an
orchestrator with several sub-agents, and asks the user how many agents and
which models before spawning anything.

Phase order is not optional. Two rules carry most of the weight:

1. **Phase 2 before phase 3.** A checker that has not reproduced the known
   small cases is untested code, and "no counterexample found" from untested
   code means nothing. Reproducing known values is also how you discover you
   misread the statement.
2. **Phase 5 before anyone sees it.** Do not tell the user "proved" or
   "disproved" until `verify-gate` passes. Before that, the honest words are
   "candidate", "sketch" or "compiles with N sorries".

## Choosing between 3a and 3b

Run cheap falsification first, almost always. Ask:

- Is the statement universally quantified over finite objects with a small
  parameter (graphs on n vertices, colourings of [n], sets in [N])? Search
  first: a counterexample is a short `decide` proof, a proof is months.
- Does it assert an asymptotic or "for all sufficiently large" bound? Code
  cannot refute it, but code can find the extremal examples and their
  structure, which suggests the proof (or a counterexample family).
- Is it an existence claim ("there exist infinitely many…")? Constructions
  come from program search (phase 3a) and then need a general proof (3b).

Keep both tracks open and let evidence move effort between them.

## State you must keep

Create `Work/<ProblemId>/NOTES.md` in the formal-conjectures checkout at the
start, and append to it at every phase transition:

```
## <date> phase N -> N+1
statement: <fully qualified Lean name>, sha256 <hash from statement_tools.py>
evidence: <what was checked, with commands to rerun>
open questions / suspicions:
dead ends (keep these — failures are data):
```

## Calibration you owe the user

- Most "open" problems a model can touch are open because nobody looked, not
  because they are hard. Expect the novelty check to find prior work; it
  usually does (see `references/professional-practice.md`).
- A plausible-reading prose proof from a model is weak evidence. Models write
  confident, wrong proofs of open problems routinely. Lean is the judge.
- If the formal statement disagrees with the source, the finding is the
  misformalisation, not the proof. Report it.
- Report failures. A negative result with the search space stated ("no
  counterexample with n ≤ 40, SAT-verified, encoding checked against known
  values for n ≤ 12") is a contribution; a vague "couldn't do it" is not.

## References

- `references/professional-practice.md` — how working mathematicians and labs
  run AI-assisted proving in 2025–2026, with sources and their reliability.
