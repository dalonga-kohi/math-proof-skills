---
name: lean-setup
description: Installs and checks the Lean 4 proving environment - elan, Lean, Lake, the formal-conjectures project with its pinned Mathlib cache, and the lean-lsp MCP server for Claude Code. Use at the start of any formal proving work, when `lake build` or imports fail, when the Lean MCP tools are missing, or when the user asks to set up Lean, Mathlib or formal-conjectures.
license: Apache-2.0
compatibility: Linux or macOS shell (Windows via WSL). Needs git, curl, ~10 GB disk for the Mathlib cache, and uv for lean-lsp-mcp.
metadata:
  version: "0.1.0"
  stack: math-proof-skills
---

# Lean setup

Goal: a formal-conjectures checkout that builds, with Claude Code able to read
live goals through the `lean-lsp` MCP server. Work *inside* that checkout so
you inherit its exact toolchain, Mathlib revision and statements.

## Fast path

```bash
bash scripts/setup.sh            # installs elan + uv if missing, clones, fetches cache, builds
bash scripts/doctor.sh           # verifies every piece; rerun whenever something feels off
```

`setup.sh` takes `FC_DIR` (default `./formal-conjectures`) and `FC_REF`
(default `main`; pin a tag such as `v4.33.1` for reproducibility). Read the
script before running it: it installs elan and uv from their official install
scripts.

## What the steps are, and why

1. **elan** manages Lean toolchains. The project's `lean-toolchain` file
   (`leanprover/lean4:v4.33.1` on main, checked 25 Nov 2026) makes elan fetch
   the right Lean automatically. Never install Lean any other way.
2. **Clone formal-conjectures** (`google-deepmind/formal-conjectures`). It
   tracks monthly Mathlib releases, and tags each bump as `v4.X.Y`.
3. **`lake exe cache get`** downloads prebuilt Mathlib `.olean` files. Skipping
   it means compiling Mathlib from source (hours). If it fails, you are almost
   always on a Mathlib revision without a cache: check `lake-manifest.json`
   was not edited.
4. **`lake build`** builds the project. Warnings about `sorry` are expected:
   that is what open problems look like.
5. **VS Code + Lean 4 extension** (from the Lean community install page) for
   the human. Infoview is the fastest way for a person to see a goal.
6. **lean-lsp-mcp**, from the project root:
   ```bash
   claude mcp add lean-lsp uvx lean-lsp-mcp          # user scope
   claude mcp add -s project lean-lsp uvx lean-lsp-mcp   # writes .mcp.json for collaborators
   ```
   Build first: the server runs `lake serve` and will be slow or wrong on an
   unbuilt project. Install ripgrep for `lean_local_search`.

## Your own work files

Put attempts in `Work/<ProblemId>/` inside the checkout. You do not need to
touch `lakefile`: from the project root, `lake env lean Work/Erdos123/Main.lean`
compiles any file against the project's dependencies, and the LSP serves any
file under the root. Do not commit `Work/` to a formal-conjectures PR.

## lean-lsp MCP tools you will use most

| Tool | Use |
|---|---|
| `lean_diagnostic_messages` | errors/warnings for a file — call after every edit |
| `lean_goal` | goal state at a line (and column) |
| `lean_multi_attempt` | try several tactics at one position without editing the file |
| `lean_leansearch`, `lean_loogle`, `lean_leanfinder` | find Mathlib lemmas by meaning, by type pattern, by informal query |
| `lean_hammer_premise` | premise suggestions for the goal at a position |
| `lean_local_search` | ripgrep over project + Mathlib sources |
| `lean_verify` | axioms used by a declaration; flags `sorryAx` |
| `lean_build` | `lake build` and LSP restart (`fetch_cache=true` available) |

The four external search tools share a hosted rate limit of 3 requests per 30
seconds each. With several agents running, run Loogle locally
(`LEAN_LOOGLE_LOCAL`, ~13 GiB RAM on first index, ~7 GiB warm) or stagger
searches. `LEAN_MCP_MAX_OUTPUT_CHARS` (default 6000) truncates long outputs.

The README warns that the tools execute project code: only point the server
at projects you trust.

## When things break

| Symptom | Likely cause | Fix |
|---|---|---|
| `unknown package 'Mathlib'` | ran `lean` instead of `lake env lean`, or wrong directory | run from the project root via `lake env` |
| cache get downloads nothing / builds Mathlib | edited manifest, or a Mathlib rev without cache | `git checkout lake-manifest.json`, `lake exe cache get` |
| `object file ... does not exist` on import | that module not built | `lake build FormalConjectures.ErdosProblems.«123»` |
| MCP tools time out | project not built, or a heavy file | build first; split the file |
| different results than CI | toolchain drift | `cat lean-toolchain`; `elan show` |
