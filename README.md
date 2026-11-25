# math-proof-skills

Agent Skills for proving or disproving open math problems with LLMs and
Lean 4, plus an orchestrated multi-agent swarm. The loop: pick a problem,
reproduce the known small cases in code, search or reason for the new case,
make Lean check the result before anyone else sees it, check it is new,
write it up.

## Install

With the open skills CLI ([skills.sh](https://skills.sh)), for Claude Code,
Codex, Cursor and other Agent Skills clients:

```bash
npx skills add dalonga-kohi/math-proof-skills                 # pick interactively
npx skills add dalonga-kohi/math-proof-skills --skill '*'     # all 12 skills
npx skills add dalonga-kohi/math-proof-skills --skill verify-gate --skill counterexample-search
```

As a Claude Code plugin (also installs the six swarm agent definitions):

```bash
claude plugin marketplace add dalonga-kohi/math-proof-skills
claude plugin install math-proof-skills@math-proof-skills
```

Install all the skills together: some scripts reuse others (`verify-gate`
imports the statement parser from `problem-intake`). Script paths in each
`SKILL.md` are relative to that skill's folder.

## The skills

| Phase | Skill | What it gives you |
|---|---|---|
| router | `math-proof-workflow` | the loop, phase gates, which skill next; digest of how professionals work |
| 0 | `lean-setup` | elan, formal-conjectures, Mathlib cache, lean-lsp MCP; `setup.sh`, `doctor.sh` |
| 1 | `problem-intake` | triage card, statement locking (`statement_tools.py`), misformalisation checklist |
| 2 | `small-cases` | two-independent-checkers harness that must reproduce known values first |
| 3a | `counterexample-search` | SAT/SMT/ILP cookbook, Schur-number SAT template, AlphaEvolve-style `evolve.py`, witness → Lean `decide` |
| 3b | `proof-blueprint` | lemma-DAG blueprint format, red-team protocol, prompt patterns |
| 4 | `lean-formalize` | compile-after-every-step loop with lean-lsp MCP, tactic ladder, pitfalls |
| 4 | `auto-prover` | leaf-lemma ladder, `extract_sorries.py`, pass@k `local_prover.py` for open-weight provers |
| 5 | `verify-gate` | `verify_gate.py`: no sorry, standard axioms only, no `native_decide`, statement unchanged (hash + `type_of%` rfl) |
| 6 | `novelty-check` | same-day literature and tracker protocol with a written log |
| 7 | `math-writeup` | forum note with AI disclosure, formal-conjectures PR with `@[formal_proof]` + Palomar, Zulip, short arXiv |
| swarm | `math-swarm` | orchestrator + N agents in rounds on a shared blackboard; asks you how many agents and which models |

## Swarm

`math-swarm` asks four questions before spawning: swarm size (Small 4,
Standard 7, Large 12, or custom), the model for reasoning roles (strategist,
referee), the model for worker roles (Lean prover, counterexample hunter,
constructor, literature scout), and the execution mode (background
subagents, experimental Agent Teams, or headless `claude -p`). Agent
definitions are in `agents/`. Round 1 is deliberately independent for
diversity; later rounds share a blackboard and reallocate by evidence. Only
the orchestrator's own `verify-gate` run counts as a result.

## Things that changed under your guide (checked 25 Nov 2026)

- **Aristotle no longer proves Lean in aristotlelib ≥ 3.** The 3.4.0 README
  says it verifies Verilog, C and Rust and not Lean;
  `uvx --from aristotlelib aristotle prove-from-file` therefore no longer works
  as written. `auto-prover` explains the options.
- The teorth AI-contributions wiki stopped updating (data as of 30 Jun 2026).
- formal-conjectures requires a Palomar registry link in `@[formal_proof]` for
  research-solved problems.

## Tested here, not tested here

Tested in a sandbox: `statement_tools.py` (extract, scaffold, hash, check);
`harness.py` (reproduces OEIS A143824 to n = 18 with brute force and CP-SAT);
`sat_template.py` (reproduces Schur numbers S(2)=4, S(3)=13); `evolve.py` with
the real `claude` CLI (greedy 27 → verified 35-element Sidon set in
{1..1000} in two generations); `verify_gate.py` and `local_prover.py` decision
logic against Lean-format output; `init_swarm.py`; skills CLI discovery
(12 skills); `claude plugin validate`.

Not tested against a real Lean install (toolchain downloads were blocked in
the build sandbox): the `lake` invocations, the `type_of%` statement check and
`#print axioms` parsing should be exercised once on your machine with
`lean-setup/scripts/doctor.sh` and a trivial proof through `verify-gate`.

## License

Apache-2.0.
