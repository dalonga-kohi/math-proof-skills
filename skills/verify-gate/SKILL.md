---
name: verify-gate
description: Mandatory verification gate before any result is reported, shared or submitted - checks the Lean file compiles with no sorry, uses only the standard axioms, contains no native_decide/axiom/unsafe tricks, and still states exactly the original theorem (hash and elaborated-type check). Use whenever a proof or disproof is believed complete, before telling the user something is "proved", before novelty checks or write-ups, and when reviewing a Lean proof produced by another agent or tool.
license: Apache-2.0
compatibility: Run from the Lean project root; needs lake on PATH and Python 3.10+. Uses problem-intake/scripts/statement_tools.py when installed alongside.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Verification gate

LLMs, and automated provers, are optimisers: they will satisfy the letter of
"make it compile" in ways you did not intend. They change the statement, add
an `axiom`, hide a `sorry` in a `decreasing_by`, use `native_decide` on a
huge computation, or prove the sorry'd original by citing itself. This gate
is the line between a draft and a result.

## Run it

```bash
python3 scripts/verify_gate.py Work/Erdos123/Main.lean           # uses Main.lock.json from intake
python3 scripts/verify_gate.py Work/Erdos123/Main.lean --json Work/Erdos123/gate.json
```

| Check | Passes when |
|---|---|
| source scan | no `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`, `extern`, `unsafe`, kernel-check skipping; metaprogramming and `#eval` produce warnings for manual review |
| statement hash | whitespace-normalised statement equals the one recorded at intake |
| compiles | `lake env lean` reports no errors in the file |
| no sorry warnings | no declaration in the file uses `sorry` |
| axioms | `#print axioms` ⊆ {`propext`, `Classical.choice`, `Quot.sound`} |
| statement matches original | `example : type_of% @Original = type_of% @Attempt := rfl` elaborates, so the elaborated propositions agree, not only the text |

Exit 0 means PASS. Anything else: report "not verified" and why. Do not
paraphrase a FAIL as "almost done".

## Interpreting results

- **Hash fails, type check passes**: whitespace-insensitive text changed but
  meaning didn't (e.g. a renamed bound variable). Still restore the original
  text — reviewers diff it.
- **Type check fails**: you proved a different statement. Stop.
- **`Lean.ofReduceBool` in axioms**: `native_decide` somewhere (possibly in a
  lemma you imported from your own files). Replace with `decide`, a smaller
  witness, or a verified checker.
- **`sorryAx`** with no `sorry` in the file: a lemma from another work file
  you import still has a `sorry`. The gate checks transitively via axioms.
- **Warnings for `#eval` / `macro` / `elab`**: read those lines. Elaboration
  -time code can add declarations; make sure none of them is load-bearing.

## Before publication (stronger checks)

- **Comparator** (`leanprover/comparator`) checks that a proof establishes a
  reference statement; Palomar uses it. Run it if available.
- **lean4checker** replays the environment through the kernel, catching
  environment manipulation by metaprograms.
- **Clean rebuild**: fresh clone, `lake exe cache get`, `lake build`, then the
  gate again. Catches stale `.olean` artefacts.
- **Second reader**: a different agent or person reads the statement in the
  file and the source problem side by side one last time.

## Reporting

Paste the gate's output (or `gate.json`) into `NOTES.md` and into any
message that claims a result. A claim without the gate output attached is
not a claim this stack makes.
