#!/usr/bin/env python3
"""Statement tools for formal-conjectures style Lean files.

Subcommands
  list     <file.lean>                      list theorem/lemma declarations with categories
  extract  <file.lean> <name>               print docstring, attributes and statement of <name>
  hash     <file.lean> <name>               sha256 of the whitespace-normalised statement
  scaffold <file.lean> <name> --root R --out O [--new-name N]
                                            write a work file that imports the problem file and
                                            restates <name> verbatim under a new name with `sorry`
  check    <work.lean> <new-name> --hash H  confirm the restated statement still has hash H

<name> may be short (erdos_123) or qualified (Erdos123.erdos_123).
Only the standard library is used. The parser is deliberately simple: it finds the
declaration header and reads the statement up to the first top-level `:=`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DECL_RE = re.compile(r"^(?P<indent>\s*)(?:(?:private|protected|noncomputable)\s+)*(?P<kind>theorem|lemma)\s+(?P<name>[^\s:({\[]+)")
NS_OPEN = re.compile(r"^\s*namespace\s+(\S+)")
NS_END = re.compile(r"^\s*end\s+(\S+)")
OPEN_BR = "([{⟨⦃"
CLOSE_BR = ")]}⟩⦄"


@dataclass
class Decl:
    kind: str
    name: str          # as written
    qualified: str     # with enclosing namespaces
    line: int          # 1-based line of the theorem keyword
    attrs: str
    doc: str
    statement: str     # everything from `theorem` up to (not including) the top-level :=
    category: str


def _strip_comments(src: str) -> str:
    """Blank out comments (keeping offsets and newlines) so brackets inside them are ignored."""
    out = list(src)
    i, n, depth = 0, len(src), 0
    while i < n:
        if src.startswith("/-", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/-", j):
                    depth += 1; j += 2
                elif src.startswith("-/", j):
                    depth -= 1; j += 2
                else:
                    j += 1
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
        elif src.startswith("--", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            i = j + 1
        else:
            i += 1
    return "".join(out)


def _statement_end(clean: str, start: int) -> int:
    depth = 0
    i = start
    while i < len(clean):
        c = clean[i]
        if c in OPEN_BR:
            depth += 1
        elif c in CLOSE_BR:
            depth -= 1
        elif depth == 0 and clean.startswith(":=", i):
            return i
        elif depth == 0 and re.match(r"\n(theorem|lemma|def|end|namespace|@\[|/--)", clean[i:i + 12]):
            return i  # malformed: no := before next decl
        i += 1
    return len(clean)


def parse(path: Path) -> list[Decl]:
    src = path.read_text(encoding="utf-8")
    clean = _strip_comments(src)
    lines = src.splitlines(keepends=True)
    offsets, acc = [], 0
    for ln in lines:
        offsets.append(acc)
        acc += len(ln)
    ns: list[str] = []
    decls: list[Decl] = []
    clean_lines = clean.splitlines(keepends=True)
    for idx, cl in enumerate(clean_lines):
        if m := NS_OPEN.match(cl):
            ns.extend(m.group(1).split("."))
            continue
        if m := NS_END.match(cl):
            parts = m.group(1).split(".")
            if ns[-len(parts):] == parts:
                del ns[-len(parts):]
            continue
        m = DECL_RE.match(cl)
        if not m:
            continue
        start = offsets[idx] + len(m.group("indent"))
        end = _statement_end(clean, start)
        statement = src[start:end].rstrip()
        # walk upwards over attributes and docstring
        j = idx - 1
        attr_lines, doc = [], ""
        def _prefix(t: str) -> bool:
            return t.strip().startswith("@[") or t.rstrip().endswith(" in")
        while j >= 0 and _prefix(lines[j]):
            if lines[j].strip().startswith("@["):
                attr_lines.insert(0, lines[j].strip())
            j -= 1
        if j >= 0 and lines[j].rstrip().endswith("-/"):
            k = j
            while k >= 0 and "/--" not in lines[k]:
                k -= 1
            if k >= 0:
                doc = "".join(lines[k:j + 1]).strip()
                j = k - 1
            while j >= 0 and _prefix(lines[j]):
                if lines[j].strip().startswith("@["):
                    attr_lines.insert(0, lines[j].strip())
                j -= 1
        attrs = " ".join(attr_lines)
        cat = re.search(r"category\s+([a-zA-Z]+(?:\s+(?:open|solved))?)", attrs)
        name = m.group("name")
        qualified = ".".join(ns + [name]) if not name.startswith("_root_.") else name[7:]
        decls.append(Decl(m.group("kind"), name, qualified, idx + 1, attrs, doc, statement,
                          cat.group(1) if cat else ""))
    return decls


def find(decls: list[Decl], name: str) -> Decl:
    hits = [d for d in decls if d.qualified == name or d.name == name or d.qualified.endswith("." + name)]
    if not hits:
        sys.exit(f"error: no theorem/lemma named {name!r}; try `list`")
    if len(hits) > 1:
        sys.exit("error: ambiguous name; use one of: " + ", ".join(d.qualified for d in hits))
    return hits[0]


def body_of(stmt: str) -> str:
    """Statement without the `theorem <name>` head, so renaming does not change the hash."""
    return re.sub(r"^\s*(?:(?:private|protected|noncomputable)\s+)*(theorem|lemma)\s+\S+", "", stmt, count=1)


def norm(stmt: str) -> str:
    return " ".join(_strip_comments(body_of(stmt)).split())


def sha(stmt: str) -> str:
    return hashlib.sha256(norm(stmt).encode()).hexdigest()


def module_name(file: Path, root: Path) -> str:
    rel = file.resolve().relative_to(root.resolve()).with_suffix("")
    parts = []
    for p in rel.parts:
        parts.append(p if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", p) else f"«{p}»")
    return ".".join(parts)


CONTEXT_RE = re.compile(r"^\s*(open\s|(local\s+|scoped\s+)?(notation|infix|infixl|infixr|prefix|postfix)\b|variable\b|set_option\s)")


def _context_lines(file: Path, decl_line: int) -> list[str]:
    """Top-level `open`, notation, `variable` and `set_option` lines before the declaration.

    They change how the statement elaborates, so the restatement must see them too.
    `open X in` / `set_option ... in` prefixes attached to the declaration are included.
    """
    lines = _strip_comments(file.read_text(encoding="utf-8")).splitlines()[: decl_line - 1]
    keep = [ln.rstrip() for ln in lines if CONTEXT_RE.match(ln) and not ln.rstrip().endswith(" in")]
    # attached `... in` prefixes directly above the declaration (possibly among attributes)
    j = decl_line - 2
    attached = []
    while j >= 0 and (lines[j].strip().startswith("@[") or lines[j].rstrip().endswith(" in") or not lines[j].strip()):
        if lines[j].rstrip().endswith(" in"):
            attached.insert(0, lines[j].rstrip()[:-3].rstrip())
        j -= 1
    return keep + attached


def cmd_scaffold(a) -> None:
    d = find(parse(Path(a.file)), a.name)
    root = Path(a.root)
    mod = module_name(Path(a.file), root)
    new = a.new_name or (d.name.replace(".", "_") + "_attempt")
    namespaces = d.qualified.split(".")[:-1]
    ns = ".".join(namespaces)
    h = sha(d.statement)
    restated = re.sub(r"^(\s*(?:(?:private|protected|noncomputable)\s+)*)(theorem|lemma)\s+\S+",
                      lambda m: f"{m.group(1)}theorem {new}", d.statement.lstrip(), count=1)
    today = _dt.date.today().isoformat()
    context = "\n".join(_context_lines(Path(a.file), d.line))
    out = f"""import {mod}

/-!
# Work file for `{d.qualified}`

Source file : {a.file}
Category    : {d.category or 'unknown'}
Copied on   : {today}
Statement sha256 (normalised, name-independent): {h}

DO NOT EDIT THE STATEMENT BELOW. Changing it proves a different theorem.
`verify-gate` checks it against the original by hash and by `type_of%` defeq.
Never use `{d.qualified}` itself in the proof: it is proved by `sorry`.
-/

{context}
{("namespace " + ns) if ns else ""}

{d.doc}
{restated} := by
  sorry

{("end " + ns) if ns else ""}
"""
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(re.sub(r"\n{3,}", "\n\n", out), encoding="utf-8")
    qualified_new = (ns + "." if ns else "") + new
    meta = {"original": d.qualified, "attempt": qualified_new, "module": mod, "sha256": h,
            "category": d.category, "copied_on": today, "source_file": a.file}
    Path(a.out).with_suffix(".lock.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("file")
    s = sub.add_parser("extract"); s.add_argument("file"); s.add_argument("name")
    s = sub.add_parser("hash"); s.add_argument("file"); s.add_argument("name")
    s = sub.add_parser("scaffold"); s.add_argument("file"); s.add_argument("name")
    s.add_argument("--root", default="."); s.add_argument("--out", required=True); s.add_argument("--new-name")
    s = sub.add_parser("check"); s.add_argument("file"); s.add_argument("name"); s.add_argument("--hash", required=True)
    a = p.parse_args()

    if a.cmd == "list":
        for d in parse(Path(a.file)):
            print(f"{d.line:5d}  {d.category or '-':16s}  {d.qualified}")
    elif a.cmd == "extract":
        d = find(parse(Path(a.file)), a.name)
        print(json.dumps({**asdict(d), "sha256": sha(d.statement)}, indent=2, ensure_ascii=False))
    elif a.cmd == "hash":
        print(sha(find(parse(Path(a.file)), a.name).statement))
    elif a.cmd == "scaffold":
        cmd_scaffold(a)
    elif a.cmd == "check":
        h = sha(find(parse(Path(a.file)), a.name).statement)
        if h != a.hash:
            print(f"STATEMENT CHANGED: {h} != {a.hash}"); sys.exit(1)
        print("statement unchanged")


if __name__ == "__main__":
    main()
