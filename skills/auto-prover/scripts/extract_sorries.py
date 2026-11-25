#!/usr/bin/env python3
"""List the declarations in a Lean file that still contain `sorry`, and optionally
split each into a standalone file for an automated prover.

    python3 extract_sorries.py Work/Erdos123/Main.lean
    python3 extract_sorries.py Work/Erdos123/Main.lean --split Work/Erdos123/leaves

Each split file is the original file truncated right after the target
declaration, so the target can use every earlier lemma (sorry'd or not) as a
black box. A prover then only has to replace the sorry in the LAST declaration.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DECL = re.compile(r"^(?:(?:private|protected|noncomputable|nonrec)\s+)*(theorem|lemma|def|abbrev|instance|example)\b\s*([^\s:({\[]*)")


def strip_comments(src: str) -> str:
    out, i, n = list(src), 0, len(src)
    while i < n:
        if src.startswith("/-", i):
            d, j = 1, i + 2
            while j < n and d:
                if src.startswith("/-", j): d += 1; j += 2
                elif src.startswith("-/", j): d -= 1; j += 2
                else: j += 1
            for k in range(i, j):
                if out[k] != "\n": out[k] = " "
            i = j
        elif src.startswith("--", i):
            j = src.find("\n", i); j = n if j == -1 else j
            for k in range(i, j): out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


def statement_head(decl: str) -> str:
    """Declaration text up to its first top-level `:=` (brackets respected, comments ignored)."""
    clean, depth = strip_comments(decl), 0
    for i, c in enumerate(clean):
        if c in "([{⟨⦃": depth += 1
        elif c in ")]}⟩⦄": depth -= 1
        elif depth == 0 and clean.startswith(":=", i):
            return decl[:i]
    return decl


def blocks(src: str) -> list[dict]:
    lines, clean = src.splitlines(keepends=True), strip_comments(src).splitlines(keepends=True)
    heads = [i for i, l in enumerate(clean) if DECL.match(l)]
    res = []
    for h_idx, h in enumerate(heads):
        start = h
        while start > 0 and (clean[start - 1].strip().startswith("@[") or lines[start - 1].rstrip().endswith("-/")
                             or clean[start - 1].rstrip().endswith(" in")):
            if lines[start - 1].rstrip().endswith("-/"):
                k = start - 1
                while k > 0 and "/-" not in lines[k]: k -= 1
                start = k
            else:
                start -= 1
        nxt = heads[h_idx + 1] if h_idx + 1 < len(heads) else len(lines)
        end = nxt
        # do not swallow the next block's docstring/attributes or a trailing `end`
        while end - 1 > h and (clean[end - 1].strip() == "" or clean[end - 1].strip().startswith("@[")
                               or re.match(r"^\s*(end|namespace|section|open|variable)\b", clean[end - 1])
                               or lines[end - 1].lstrip().startswith(("/--", "-/")) or "/--" in lines[end - 1]):
            end -= 1
        m = DECL.match(clean[h])
        body = "".join(clean[h:end])
        res.append({"kind": m.group(1), "name": m.group(2) or "(anonymous)", "start": start + 1, "head": h + 1,
                    "end": end, "sorries": len(re.findall(r"\bsorry\b", body))})
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file"); ap.add_argument("--split"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    src = Path(a.file).read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    todo = [b for b in blocks(src) if b["sorries"]]
    if a.json:
        print(json.dumps(todo, indent=2))
    else:
        for b in todo:
            print(f"line {b['head']:5d}  {b['kind']:8s} {b['name']}  ({b['sorries']} sorry)")
        print(f"{len(todo)} declaration(s) with sorry")
    if a.split:
        out = Path(a.split); out.mkdir(parents=True, exist_ok=True)
        for b in todo:
            safe = re.sub(r"[^A-Za-z0-9_.]", "_", b["name"])
            p = out / f"{b['head']:05d}_{safe}.lean"
            p.write_text("".join(lines[: b["end"]]), encoding="utf-8")
            print(f"wrote {p}")


if __name__ == "__main__":
    main()
