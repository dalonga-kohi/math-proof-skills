#!/usr/bin/env python3
"""Minimal LLM-guided program search (AlphaEvolve / FunSearch style).

An LLM rewrites programs; a trusted evaluator scores what they output. The
LLM never sees or touches the evaluator's verdict logic, and candidate code
runs in a separate process with a timeout.

Files you provide
  task.md        what to construct and what the score means
  seed.py        defines construct() -> JSON-serialisable object
  evaluate.py    defines score(obj) -> float, raising ValueError if obj is invalid

Usage
  python3 evolve.py --dir examples/sidon --backend claude --model sonnet --generations 30
  python3 evolve.py --dir examples/sidon --backend openai --base-url http://localhost:8000/v1 --model qwen
  python3 evolve.py --dir examples/sidon --backend echo --generations 2    # pipeline smoke test

Outputs in <dir>/runs/: pool.jsonl (every candidate), best.py, best.json.
Treat best.json as a candidate until an independent checker (and ideally
Lean, see references/certificate-to-lean.md) confirms it.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RUN_CANDIDATE = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("cand", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
json.dump(m.construct(), open(sys.argv[2], "w"))
"""
RUN_EVAL = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("ev", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(json.dumps({"score": float(m.score(json.load(open(sys.argv[2]))))}))
"""

PROMPT = """You are improving a program in an evolutionary search for a mathematical construction.

# Task
{task}

# Current programs (best first) with their scores
{programs}

# Instructions
Write ONE new complete Python program defining `construct()` that should score higher than
all programs above. Prefer a genuinely different idea over tweaking constants: algebraic
constructions, greedy with a new ordering, local search, products/lifts of small optima.
It must run in under {timeout} seconds with only the standard library{extra_libs}.
Return only the program in a single ```python code block.
"""


def call_llm(backend: str, prompt: str, model: str, base_url: str) -> str:
    if backend == "echo":
        return ""
    if backend == "claude":
        r = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "text"],
                           capture_output=True, text=True, timeout=900)
        return r.stdout
    if backend == "openai":
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "temperature": 1.0}).encode()
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", "none")})
        with urllib.request.urlopen(req, timeout=900) as resp:
            return json.load(resp)["choices"][0]["message"]["content"]
    raise ValueError(backend)


def extract_code(text: str) -> str | None:
    m = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return m[-1] if m else None


def evaluate(code: str, evaluator: Path, timeout: int) -> tuple[float | None, str]:
    with tempfile.TemporaryDirectory() as td:
        cand, out = Path(td, "cand.py"), Path(td, "out.json")
        cand.write_text(code)
        try:
            r = subprocess.run([sys.executable, "-I", "-c", RUN_CANDIDATE, str(cand), str(out)],
                               capture_output=True, text=True, timeout=timeout, cwd=td)
        except subprocess.TimeoutExpired:
            return None, "timeout"
        if r.returncode != 0 or not out.exists():
            return None, "crash: " + r.stderr[-500:]
        try:
            e = subprocess.run([sys.executable, "-I", "-c", RUN_EVAL, str(evaluator), str(out)],
                               capture_output=True, text=True, timeout=max(60, timeout))
        except subprocess.TimeoutExpired:
            return None, "evaluator timeout"
        if e.returncode != 0:
            return None, "invalid: " + e.stderr.strip().splitlines()[-1][:300] if e.stderr.strip() else "invalid"
        return json.loads(e.stdout)["score"], "ok"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--backend", choices=["claude", "openai", "echo"], default="claude")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--show", type=int, default=3, help="programs shown in each prompt")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--extra-libs", default="", help="e.g. ', numpy'")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    random.seed(a.seed)

    d = Path(a.dir); runs = d / "runs"; runs.mkdir(exist_ok=True)
    task = (d / "task.md").read_text()
    evaluator = (d / "evaluate.py").resolve()
    pool_file = runs / "pool.jsonl"

    pool: list[dict] = []
    if pool_file.exists():
        pool = [json.loads(l) for l in pool_file.read_text().splitlines() if l.strip()]
    if not any(p["score"] is not None for p in pool):
        code = (d / "seed.py").read_text()
        s, msg = evaluate(code, evaluator, a.timeout)
        if s is None:
            sys.exit(f"seed program fails: {msg}")
        pool.append({"gen": 0, "score": s, "status": msg, "code": code})
        pool_file.write_text(json.dumps(pool[-1]) + "\n")
        print(f"seed score {s}")

    for g in range(1, a.generations + 1):
        valid = sorted((p for p in pool if p["score"] is not None), key=lambda p: -p["score"])
        # parent: best with prob 0.5, else a random member of the top 10 (keeps diversity)
        shown = [valid[0]] if random.random() < 0.5 else [random.choice(valid[:10])]
        shown += [p for p in valid[: a.show + 1] if p is not shown[0]][: a.show - 1]
        progs = "\n\n".join(f"## score = {p['score']}\n```python\n{p['code']}\n```" for p in shown)
        prompt = PROMPT.format(task=task, programs=progs, timeout=a.timeout, extra_libs=a.extra_libs)
        t = time.time()
        try:
            reply = call_llm(a.backend, prompt, a.model, a.base_url)
        except Exception as e:  # network or CLI failure: log and continue
            reply = ""; print(f"gen {g}: LLM call failed: {e}")
        code = extract_code(reply) or (shown[0]["code"] if a.backend == "echo" else None)
        if code is None:
            entry = {"gen": g, "score": None, "status": "no code in reply", "code": ""}
        else:
            s, msg = evaluate(code, evaluator, a.timeout)
            entry = {"gen": g, "score": s, "status": msg, "code": code}
        pool.append(entry)
        with pool_file.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
        best = max((p for p in pool if p["score"] is not None), key=lambda p: p["score"])
        print(f"gen {g:3d}  score={entry['score']}  status={entry['status'][:60]}  best={best['score']}  ({time.time()-t:.0f}s)")
        (runs / "best.py").write_text(best["code"])

    best = max((p for p in pool if p["score"] is not None), key=lambda p: p["score"])
    with tempfile.TemporaryDirectory() as td:
        cand, out = Path(td, "c.py"), Path(td, "o.json")
        cand.write_text(best["code"])
        subprocess.run([sys.executable, "-I", "-c", RUN_CANDIDATE, str(cand), str(out)], timeout=a.timeout, cwd=td)
        (runs / "best.json").write_text(out.read_text())
    print(f"best score {best['score']}  -> {runs/'best.py'}, {runs/'best.json'}")


if __name__ == "__main__":
    main()
