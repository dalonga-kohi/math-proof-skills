---
name: math-swarm
description: Runs a swarm of AI agents on one math problem - an orchestrator plus several sub-agents (strategists on distinct proof angles, counterexample hunters, a construction searcher, Lean provers, a literature scout, a hostile referee) working in rounds on a shared blackboard, with Lean as the only judge. Asks the user how many agents and which models to use before spawning. Use when the user wants multiple agents, parallel approaches, a team or swarm, or when a single line of attack has stalled.
license: Apache-2.0
compatibility: Best in Claude Code (Agent tool, background subagents, optional experimental Agent Teams, or headless `claude -p`). Needs the other math-proof-skills installed and a built Lean project.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Math swarm (orchestrator)

You are the orchestrator. You do not prove things yourself during a swarm:
you brief, assign, merge, verify and reallocate. Sub-agents produce
candidates; only artefacts that pass your own re-check count.

## 0. Preconditions

- `problem-intake` done: locked work file + `Main.lock.json`.
- `small-cases` harness passing, or assign it as the first task to one agent
  and wait: nothing else is trustworthy until it passes.

## 1. Ask the user before spawning anything

Use the AskUserQuestion tool if you have it; otherwise ask in one message and
wait. Ask all of these:

1. **How many agents?**
   - Small — 4: strategist, counterexample hunter, Lean prover, referee
   - Standard — 7 (recommended): 2 strategists, hunter, constructor, Lean prover, literature scout, referee
   - Large — 12: 4 strategists, 2 hunters, constructor, 3 Lean provers, scout, referee
   - Custom: the user gives role counts
2. **Model for reasoning roles** (strategists, referee): `opus` (recommended
   for open problems), `sonnet`, `fable`, or `inherit` (same as this session).
3. **Model for worker roles** (Lean provers, hunters, constructor, scout):
   `sonnet` (recommended: many compile-edit iterations), `opus`, `haiku`
   (cheap; fine for scripted search and scouting leads), or `inherit`.
4. **Execution mode**: background subagents (recommended; works everywhere),
   Agent Teams (experimental; needs `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   and an interactive session; teammates can message each other), or headless
   `claude -p` processes (scales past one session; runs unattended).

State the defaults you will use for anything else: 3 rounds maximum, stop
early on a gate PASS or a referee-confirmed fatal obstruction. Tell the user
that cost grows roughly linearly with agent count.

The model recommendations are heuristics, not measurements: strong models
matter most where one idea decides everything (strategy, refereeing), and
throughput matters most in Lean edit-compile loops.

## 2. Initialise the shared workspace

```bash
python3 scripts/init_swarm.py --id Erdos123 --work-file Work/Erdos123/Main.lean \
    --size standard --reasoning-model opus --worker-model sonnet
```

This writes `Work/Erdos123/swarm/`: `brief.md` (problem, locked statement,
small-case data, rules), `blackboard.md`, `ledger.jsonl`, `plan.json`, and one
folder per agent with its `assignment.md` and, for provers, a private copy of
the Lean file. Edit the angles in `plan.json` if you have better ones.

Workspace rules that keep agents from colliding:
- Each agent writes only inside its own folder. You alone write `Main.lean`,
  `blackboard.md` and the ledger.
- No git worktrees for Lean agents: each worktree would need its own Mathlib
  build cache (gigabytes). Separate files in one project are enough.
- Only you run `lake build`. Agents check with `lean_diagnostic_messages` or
  `lake env lean <their file>`.
- The hosted Lean search tools allow 3 requests / 30 s each, shared by all
  agents. Tell agents to prefer `lean_local_search`, or run Loogle locally.

## 3. Spawn

Per agent, send its `assignment.md` contents as the prompt.

- **Subagents**: Agent tool, `subagent_type` = the role's agent
  (`swarm-strategist`, `swarm-counterexample-hunter`, `swarm-constructor`,
  `swarm-lean-prover`, `swarm-literature-scout`, `swarm-referee`; prefixed
  `math-proof-skills:` when installed as a plugin; `general-purpose` with the
  role text from `references/roles.md` if the agent files are not
  installed), `model` = the user's choice for that role,
  `run_in_background: true`. Launch all of a round's agents in one message.
- **Agent Teams**: ask to spawn named teammates with those agent types; put
  each blueprint lemma on the shared task list so provers self-claim.
- **Headless**: `bash scripts/swarm_headless.sh Work/Erdos123/swarm` launches
  one `claude -p` per agent from `plan.json` and collects JSON output.

## 4. Rounds

**Round 1 — independent exploration.** Strategists each get one distinct
angle; hunters different encodings; the scout searches literature; the
referee waits. Agents do not read the blackboard in round 1: independent
attempts give diversity, shared notes give convergence, and you want
diversity first.

**Merge (you).** For every report (schema in `references/roles.md`):
1. Re-check the artefact yourself: run the script, compile the file, rerun
   the checker. Unchecked claims go on the blackboard as "claimed".
2. Append the report to `ledger.jsonl`; update `blackboard.md` with verified
   facts, refuted approaches (with the reason), open leads.
3. Anything claiming proved/disproved → `verify-gate` now. A counterexample
   → independent re-check + `counterexample-search` "when you find something".

**Round 2+ — focus.** Reallocate by evidence, roughly successive halving:
- The best 1–2 blueprints go to the referee first, then to provers, lemmas
  split among provers (each proves its lemmas in its own copy; you merge).
- Agents whose angle hit a solid obstruction get a new angle or a supporting
  job (testing lemmas numerically, searching Mathlib, shrinking a witness).
- Now everyone reads the blackboard.
- Always keep one agent on the opposite track (if most are proving, one keeps
  hunting counterexamples, and vice versa).

**Stop** on: gate PASS (→ `novelty-check`); a referee-confirmed fatal flaw in
every live approach; or the round budget. Then write a final blackboard
summary including dead ends: that is a result too.

## 5. Orchestrator discipline

- Never forward an agent's "proved" to the user before `verify-gate` passes.
- Disagreement between agents is information; send it to the referee rather
  than averaging opinions.
- Watch for statement drift: a prover that "simplified" the statement is
  rejected regardless of what it proved.
- Keep the user informed in short lines between rounds: what each agent
  found, what you verified, what you are reallocating and why.

## References

- `references/roles.md` — role prompts, the report schema, angle catalogue.
