#!/usr/bin/env python3
"""Create the shared workspace for a math swarm.

    python3 init_swarm.py --id Erdos123 --work-file Work/Erdos123/Main.lean \
        --size standard --reasoning-model opus --worker-model sonnet
    python3 init_swarm.py --id Erdos123 --work-file ... --roles strategist:3,lean-prover:2,referee:1

Writes Work/<id>/swarm/{brief.md, blackboard.md, ledger.jsonl, plan.json, <agent>/assignment.md}
and a private Lean copy for each lean-prover. Safe to re-run: existing agent
folders are kept, assignments are rewritten.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SIZES = {
    "small": {"strategist": 1, "counterexample-hunter": 1, "lean-prover": 1, "referee": 1},
    "standard": {"strategist": 2, "counterexample-hunter": 1, "constructor": 1, "lean-prover": 1,
                 "literature-scout": 1, "referee": 1},
    "large": {"strategist": 4, "counterexample-hunter": 2, "constructor": 1, "lean-prover": 3,
              "literature-scout": 1, "referee": 1},
}
REASONING = {"strategist", "referee"}
ANGLES = {
    "strategist": ["minimal counterexample / induction with the right generalisation",
                   "probabilistic method (moments, alterations, LLL, entropy)",
                   "algebraic (polynomial method, linear algebra bounds, characters)",
                   "reduction to or generalisation of a known theorem",
                   "analytic (generating functions, Fourier / density increment, sieve)",
                   "extremal combinatorics (shifting, compression, stability)",
                   "explicit construction for the existence / lower-bound side"],
    "counterexample-hunter": ["SAT via PySAT/CaDiCaL with certified UNSAT", "brute force with canonical augmentation",
                              "ILP / CP-SAT", "SMT (Z3)"],
    "constructor": ["LLM-guided program search with evolve.py"],
    "lean-prover": ["lemmas assigned by the orchestrator after round 1 (until then: build the skeleton and close routine lemmas)"],
    "literature-scout": ["prior work on the problem, special cases and the key lemmas"],
    "referee": ["attack blueprints and claimed proofs; audit statement fidelity"],
}
AGENT_TYPE = {r: f"swarm-{r}" for r in ANGLES}

COMMON = """You are one agent in a swarm working on a single math problem.
Read {swarm}/brief.md first. Rules:
- Write only inside {swarm}/{name}/. Never edit the locked statement.
- Never run `lake build`; check Lean with lean_diagnostic_messages or `lake env lean <your file>`.
- Prefer lean_local_search; hosted Lean search is shared and rate-limited (3 requests / 30 s per tool).
- "Proved"/"disproved" needs an artefact the orchestrator can check in a minute. If unsure, report
  partial or obstruction: those are good outcomes.
- {blackboard}
- End your final message with the JSON report block from math-swarm/references/roles.md, nothing after it.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True)
    ap.add_argument("--work-file", required=True)
    ap.add_argument("--size", choices=SIZES, default="standard")
    ap.add_argument("--roles", help="override, e.g. strategist:3,lean-prover:2,referee:1")
    ap.add_argument("--reasoning-model", default="opus")
    ap.add_argument("--worker-model", default="sonnet")
    ap.add_argument("--round", type=int, default=1)
    a = ap.parse_args()

    work = Path(a.work_file)
    swarm = work.parent / "swarm"
    swarm.mkdir(parents=True, exist_ok=True)
    roles = dict(SIZES[a.size])
    if a.roles:
        roles = {k: int(v) for k, v in (p.split(":") for p in a.roles.split(","))}
        unknown = set(roles) - set(ANGLES)
        if unknown:
            raise SystemExit(f"unknown roles: {unknown}; choose from {sorted(ANGLES)}")

    lock = work.with_suffix(".lock.json")
    lock_info = json.loads(lock.read_text()) if lock.exists() else {}
    notes = work.parent / "NOTES.md"
    small = work.parent / "small_cases.json"

    brief = swarm / "brief.md"
    if not brief.exists():
        brief.write_text(f"""# Swarm brief: {a.id}

## Locked statement
File: {work}
Original: {lock_info.get('original', '?')}   Attempt: {lock_info.get('attempt', '?')}
sha256: {lock_info.get('sha256', '?')}
(Paste the informal statement and the source link here.)

## Known small cases
{'See ' + str(small) if small.exists() else '(fill in: table + source, and the validated checker script path)'}

## What is already known / tried
{'See ' + str(notes) if notes.exists() else '(fill in)'}

## Rules
Lean is the only judge. Nothing is "proved" until verify-gate passes on the orchestrator's machine.
""")
    (swarm / "blackboard.md").touch()
    (swarm / "ledger.jsonl").touch()

    agents = []
    for role, count in roles.items():
        for i in range(1, count + 1):
            name = f"{role}-{i}"
            d = swarm / name
            d.mkdir(exist_ok=True)
            angle = ANGLES[role][(i - 1) % len(ANGLES[role])]
            model = a.reasoning_model if role in REASONING else a.worker_model
            lean_copy = None
            if role == "lean-prover" and work.exists():
                lean_copy = d / work.name
                if not lean_copy.exists():
                    shutil.copy(work, lean_copy)
            bb = ("Round 1: do NOT read blackboard.md; work independently."
                  if a.round == 1 else f"Read {swarm}/blackboard.md before starting.")
            text = COMMON.format(swarm=swarm, name=name, blackboard=bb)
            text += f"\nYour name: {name}\nYour role: {role}\nYour assignment: {angle}\n"
            if lean_copy:
                text += f"Your private Lean file: {lean_copy}\n"
            (d / "assignment.md").write_text(text)
            agents.append({"name": name, "role": role, "agent_type": AGENT_TYPE[role], "model": model,
                           "assignment": angle, "dir": str(d), "prompt_file": str(d / "assignment.md")})

    plan = {"id": a.id, "round": a.round, "work_file": str(work), "swarm_dir": str(swarm), "agents": agents}
    (swarm / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(f"{len(agents)} agents -> {swarm}/plan.json")
    for ag in agents:
        print(f"  {ag['name']:26s} {ag['model']:8s} {ag['assignment']}")


if __name__ == "__main__":
    main()
