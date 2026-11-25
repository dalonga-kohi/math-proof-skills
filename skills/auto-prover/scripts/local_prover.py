#!/usr/bin/env python3
"""Pass@k loop for an open-weight Lean prover behind an OpenAI-compatible server
(vLLM, SGLang, llama.cpp server), with Lean as the judge.

    vllm serve deepseek-ai/DeepSeek-Prover-V2-7B --port 8000        # or Goedel-Prover-V2, Kimina-Prover
    python3 local_prover.py leaves/00042_my_lemma.lean --project . \
        --base-url http://localhost:8000/v1 --model deepseek-ai/DeepSeek-Prover-V2-7B -k 16

The target is the LAST declaration in the file (as produced by extract_sorries.py --split).
A candidate is accepted only if
  * it restates the target statement unchanged (whitespace-insensitive),
  * it contains no sorry/admit/axiom/native_decide, and
  * `lake env lean` reports no errors and no sorry warning at or after the target line.
Accepted proofs are written to <file>.proved.lean. Run verify-gate on the
spliced result afterwards; this script is a filter, not the gate.

Prompt templates are approximations of each model card's recommended format;
check the card of the exact checkpoint you serve.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_sorries import blocks, statement_head, strip_comments  # noqa: E402

TEMPLATES = {
    "deepseek": ("Complete the following Lean 4 code:\n\n```lean4\n{code}\n```\n\n"
                 "Before producing the Lean 4 code to formally prove the given theorem, provide a detailed "
                 "proof plan outlining the main proof steps and strategies.\nThe plan should highlight key ideas, "
                 "intermediate lemmas, and proof structures that will guide the construction of the final formal proof."),
    "goedel": ("Complete the following Lean 4 code:\n\n```lean4\n{code}\n```\n\n"
               "Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan "
               "outlining the main proof steps and strategies."),
    "kimina": ("Think about and solve the following problem step by step in Lean 4.\n"
               "# Formal statement:\n```lean4\n{code}\n```\n"),
    "plain": ("Replace the final `sorry` in this Lean 4 + Mathlib file with a complete proof. Do not change any "
              "statement. Earlier lemmas may be used as given.\n\n```lean4\n{code}\n```\n"
              "Return the full file in one ```lean4 block."),
}
FORBIDDEN = re.compile(r"\b(sorry|admit|native_decide)\b|^\s*axiom\s", re.M)


def norm(s: str) -> str:
    return " ".join(strip_comments(s).split())


def ask(base_url: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", "none")})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file"); ap.add_argument("--project", default=".")
    ap.add_argument("--base-url", default="http://localhost:8000/v1"); ap.add_argument("--model", required=True)
    ap.add_argument("--template", choices=TEMPLATES, default="deepseek")
    ap.add_argument("-k", type=int, default=8); ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--temperature", type=float, default=1.0)
    a = ap.parse_args()

    src = Path(a.file).read_text(encoding="utf-8")
    target = blocks(src)[-1]
    lines = src.splitlines(keepends=True)
    prefix = "".join(lines[: target["head"] - 1])
    target_text = "".join(lines[target["head"] - 1: target["end"]])
    stmt = norm(statement_head(target_text))

    for i in range(1, a.k + 1):
        try:
            reply = ask(a.base_url, a.model, TEMPLATES[a.template].format(code=src), a.max_tokens, a.temperature)
        except Exception as e:
            print(f"[{i}] request failed: {e}"); continue
        codes = re.findall(r"```lean4?\n(.*?)```", reply, re.S)
        if not codes:
            print(f"[{i}] no code block"); continue
        cand = codes[-1]
        cblocks = [b for b in blocks(cand) if b["name"] == target["name"]]
        if not cblocks:
            print(f"[{i}] target declaration missing"); continue
        cl = cand.splitlines(keepends=True)
        new_decl = "".join(cl[cblocks[-1]["head"] - 1: cblocks[-1]["end"]])
        if norm(statement_head(new_decl)) != stmt:
            print(f"[{i}] statement was changed: rejected"); continue
        if FORBIDDEN.search(strip_comments(new_decl)):
            print(f"[{i}] forbidden construct: rejected"); continue
        full = prefix + new_decl
        with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False, dir=Path(a.file).parent) as t:
            t.write(full); tp = t.name
        try:
            r = subprocess.run(["lake", "env", "lean", tp], cwd=a.project, capture_output=True, text=True, timeout=600)
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            out = "error: timeout"
        finally:
            Path(tp).unlink(missing_ok=True)
        start = target["head"]
        errs = re.findall(r":(\d+):\d+: error", out) or (["?"] if "error: timeout" in out else [])
        late_sorry = [l for l in re.findall(r":(\d+):\d+: warning: declaration uses 'sorry'", out) if int(l) >= start]
        if not errs and not late_sorry:
            outp = Path(a.file).with_suffix(".proved.lean")
            outp.write_text(full, encoding="utf-8")
            print(f"[{i}] PROVED -> {outp}")
            return 0
        print(f"[{i}] lean rejected ({len(errs)} errors, {len(late_sorry)} sorry)")
    print("no proof found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
