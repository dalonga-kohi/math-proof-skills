#!/usr/bin/env bash
# Health check for the proving environment. Run from the formal-conjectures root.
# Exit code = number of failed checks.
set -uo pipefail

fail=0
ok()   { printf '  [ok]   %s\n' "$*"; }
bad()  { printf '  [FAIL] %s\n' "$*"; fail=$((fail+1)); }
warn() { printf '  [warn] %s\n' "$*"; }

echo "Environment"
command -v elan >/dev/null && ok "elan $(elan --version 2>/dev/null | head -1)" || bad "elan missing"
command -v lake >/dev/null && ok "lake on PATH" || bad "lake missing (source ~/.elan/env)"
command -v uvx  >/dev/null && ok "uvx on PATH"  || bad "uvx missing (install uv)"
command -v rg   >/dev/null && ok "ripgrep"      || warn "ripgrep missing (lean_local_search disabled)"
command -v python3 >/dev/null && ok "python3 $(python3 -c 'import sys;print(sys.version.split()[0])')" || bad "python3 missing"

echo "Project"
if [ -f lean-toolchain ] && [ -d FormalConjectures ]; then
  ok "in formal-conjectures root; toolchain $(cat lean-toolchain)"
else
  bad "not in a formal-conjectures root (no lean-toolchain / FormalConjectures/)"
fi
if [ -n "$(git status --porcelain lake-manifest.json lean-toolchain 2>/dev/null)" ]; then
  bad "lake-manifest.json or lean-toolchain modified: you are no longer on the pinned Mathlib"
else
  ok "toolchain and manifest untouched"
fi
[ -d .lake/packages/mathlib/.lake/build ] && ok "Mathlib build artefacts present" \
  || bad "Mathlib not built/cached: run 'lake exe cache get'"

echo "Smoke test (compiles a one-line Mathlib file)"
tmp="$(mktemp -d)/Smoke.lean"
printf 'import Mathlib\nexample : (2:ℕ) + 2 = 4 := by norm_num\n' > "$tmp"
if out=$(lake env lean "$tmp" 2>&1); then ok "Mathlib import + norm_num"; else bad "smoke test failed: $out"; fi

echo "Claude Code MCP"
if command -v claude >/dev/null; then
  claude mcp list 2>/dev/null | grep -q 'lean-lsp' && ok "lean-lsp registered" \
    || bad "lean-lsp not registered: claude mcp add lean-lsp uvx lean-lsp-mcp"
else
  warn "claude CLI not found (skip if using another agent)"
fi

echo "Optional services"
[ -n "${ARISTOTLE_API_KEY:-}" ] && ok "ARISTOTLE_API_KEY set" || warn "ARISTOTLE_API_KEY unset (see auto-prover skill: aristotlelib>=3 no longer proves Lean)"

echo
[ "$fail" -eq 0 ] && echo "All required checks passed." || echo "$fail required check(s) failed."
exit "$fail"
