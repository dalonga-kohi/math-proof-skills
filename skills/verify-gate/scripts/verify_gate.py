#!/usr/bin/env python3
"""Verification gate: nothing leaves the lab until this exits 0.

Checks, in order
  1. source scan       no sorry/admit/axiom/native_decide/implemented_by/extern/unsafe/
                       kernel-skipping options; warns on metaprogramming
  2. statement lock    normalised statement hash equals the hash recorded at intake
  3. compile           `lake env lean` on a copy of the file with checks appended:
                       - no errors, no "declaration uses 'sorry'"
                       - `#print axioms` ⊆ {propext, Classical.choice, Quot.sound}
                       - `type_of% @Original = type_of% @Attempt := rfl` (elaborated statements agree)

Usage (from the Lean project root)
  python3 verify_gate.py Work/Erdos123/Main.lean                 # reads Main.lock.json
  python3 verify_gate.py Work/Erdos123/Main.lean --theorem Erdos123.erdos_123_attempt \
      --original Erdos123.erdos_123 --sha256 <hash>
  add --json report.json to save a machine-readable report.

Exit status 0 = PASS, 1 = FAIL, 2 = usage error.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}

# (regex on comment-stripped source, message, fatal?)
SCAN = [
    (r"\bsorry\b", "uses sorry", True),
    (r"\badmit\b", "uses admit", True),
    (r"^\s*(private\s+)?axiom\s", "declares an axiom", True),
    (r"\bnative_decide\b", "uses native_decide (trusts the compiler; axiom Lean.ofReduceBool)", True),
    (r"implemented_by", "uses @[implemented_by]", True),
    (r"@\[\s*extern", "uses @[extern]", True),
    (r"\bunsafe\b", "uses unsafe", True),
    (r"debug\.skipKernelTC|skipKernelTC", "disables kernel type checking", True),
    (r"\bopaque\b", "declares an opaque constant (check it is not hiding a proof)", False),
    (r"^\s*(macro|macro_rules|elab|elab_rules|syntax|initialize)\b", "defines metaprograms (review by hand)", False),
    (r"\brun_cmd\b|\brun_tac\b|#eval", "runs code at elaboration time (review by hand)", False),
    (r"maxHeartbeats\s+0\b", "disables the heartbeat limit", False),
]


_ST = None


def load_statement_tools() -> object | None:
    """Reuse the parser from the problem-intake skill (installed alongside this one)."""
    global _ST
    if _ST is not None:
        return _ST
    here = Path(__file__).resolve()
    cand = here.parents[2] / "problem-intake" / "scripts" / "statement_tools.py"
    if not cand.exists():
        return None
    spec = importlib.util.spec_from_file_location("statement_tools", cand)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["statement_tools"] = mod
    spec.loader.exec_module(mod)
    _ST = mod
    return mod


def strip_comments(src: str) -> str:
    st = load_statement_tools()
    if st:
        return st._strip_comments(src)
    src = re.sub(r"/-.*?-/", " ", src, flags=re.S)
    return re.sub(r"--[^\n]*", " ", src)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--theorem", help="fully qualified name of the proved theorem")
    ap.add_argument("--original", help="fully qualified name of the original (sorry) statement")
    ap.add_argument("--sha256", help="statement hash recorded at intake")
    ap.add_argument("--lock", help="lock file from statement_tools scaffold (default: <file>.lock.json)")
    ap.add_argument("--project", default=".", help="Lean project root (run lake from here)")
    ap.add_argument("--allow-native", action="store_true", help="downgrade native_decide to a warning (exploration only)")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--json")
    a = ap.parse_args()

    f = Path(a.file)
    if not f.exists():
        print(f"no such file: {f}"); return 2
    lock_path = Path(a.lock) if a.lock else f.with_suffix(".lock.json")
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    thm = a.theorem or lock.get("attempt")
    orig = a.original or lock.get("original")
    sha = a.sha256 or lock.get("sha256")
    if not thm:
        print("need --theorem (or a lock file)"); return 2

    report = {"file": str(f), "theorem": thm, "original": orig, "checks": [], "warnings": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        report["checks"].append({"check": name, "ok": ok, "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))

    print(f"verify-gate: {f}  theorem={thm}")
    src = f.read_text(encoding="utf-8")
    clean = strip_comments(src)

    # 1. source scan
    fatal_hits = []
    for rx, msg, fatal in SCAN:
        if fatal and a.allow_native and "native_decide" in rx:
            fatal = False
        lines = [i + 1 for i, ln in enumerate(clean.splitlines()) if re.search(rx, ln)]
        if lines:
            (fatal_hits.append if fatal else report["warnings"].append)(f"{msg} (lines {lines[:10]})")
    check("source scan", not fatal_hits, "; ".join(fatal_hits))
    for w in report["warnings"]:
        print(f"  [warn] {w}")

    # 2. statement hash
    st = load_statement_tools()
    if sha and st:
        try:
            got = st.sha(st.find(st.parse(f), thm.split(".")[-1]).statement)
            check("statement hash", got == sha, "" if got == sha else f"{got} != recorded {sha}")
        except SystemExit as e:
            check("statement hash", False, f"could not locate theorem: {e}")
    else:
        report["warnings"].append("statement hash not checked (no --sha256/lock)")
        print("  [warn] statement hash not checked (no --sha256/lock)")

    # 3. compile with appended checks
    probe = f.with_name(f".gate_{f.stem}.lean")
    tail = f"\n\n#print axioms {thm}\n"
    if orig:
        tail += f"\nexample : type_of% @{orig} = type_of% @{thm} := rfl\n"
    probe.write_text(src + tail, encoding="utf-8")
    probe_lines = src.count("\n") + 1
    try:
        r = subprocess.run(["lake", "env", "lean", str(probe.resolve())], cwd=a.project,
                           capture_output=True, text=True, timeout=a.timeout)
        out = r.stdout + r.stderr
    except FileNotFoundError:
        out, r = "lake not found on PATH", None
    except subprocess.TimeoutExpired:
        out, r = f"timeout after {a.timeout}s", None
    finally:
        probe.unlink(missing_ok=True)
    report["lean_output"] = out[-20000:]

    msgs = re.findall(r":(\d+):\d+: (error|warning): (.*)", out)
    errors_src = [m for m in msgs if m[1] == "error" and int(m[0]) <= probe_lines]
    errors_probe = [m for m in msgs if m[1] == "error" and int(m[0]) > probe_lines]
    sorry_w = [m for m in msgs if "declaration uses 'sorry'" in m[2]]
    check("compiles", r is not None and not errors_src and (r.returncode == 0 or errors_probe),
          "; ".join(f"line {l}: {m}" for l, _, m in errors_src[:5]) or ("" if r else out[:300]))
    check("no sorry warnings", not sorry_w, f"{len(sorry_w)} declaration(s) use sorry" if sorry_w else "")

    ax_m = re.search(r"'" + re.escape(thm) + r"' depends on axioms: \[([^\]]*)\]", out)
    no_ax = re.search(r"'" + re.escape(thm) + r"' does not depend on any axioms", out)
    if ax_m or no_ax:
        axioms = {x.strip() for x in ax_m.group(1).replace("\n", " ").split(",")} if ax_m else set()
        bad = axioms - ALLOWED_AXIOMS
        if a.allow_native:
            bad.discard("Lean.ofReduceBool")
        report["axioms"] = sorted(axioms)
        check("axioms", not bad, f"{sorted(axioms)}" + (f"  NOT ALLOWED: {sorted(bad)}" if bad else ""))
    else:
        check("axioms", False, "could not read #print axioms output")

    if orig:
        lock_err = [m for m in errors_probe]
        check("statement matches original (type_of% rfl)", not lock_err and r is not None,
              "; ".join(m[2] for m in lock_err[:3]))
    else:
        report["warnings"].append("original statement not given: elaborated-statement check skipped")
        print("  [warn] original statement not given: elaborated-statement check skipped")

    passed = all(c["ok"] for c in report["checks"])
    report["result"] = "PASS" if passed else "FAIL"
    print(f"\nRESULT: {report['result']}")
    if passed:
        print("For publication also run: lean4checker (kernel replay) and leanprover/comparator against the original statement.")
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
