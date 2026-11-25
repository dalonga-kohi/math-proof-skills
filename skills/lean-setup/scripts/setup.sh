#!/usr/bin/env bash
# Set up formal-conjectures + Mathlib cache + lean-lsp-mcp.
# Usage: FC_DIR=./formal-conjectures FC_REF=main bash setup.sh
set -euo pipefail

FC_DIR="${FC_DIR:-./formal-conjectures}"
FC_REF="${FC_REF:-main}"
FC_URL="${FC_URL:-https://github.com/google-deepmind/formal-conjectures.git}"

say() { printf '\n==> %s\n' "$*"; }

if ! command -v elan >/dev/null 2>&1; then
  say "Installing elan (Lean toolchain manager)"
  curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain none
  # shellcheck disable=SC1091
  source "$HOME/.elan/env"
fi

if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv (needed for uvx lean-lsp-mcp)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ ! -d "$FC_DIR/.git" ]; then
  say "Cloning formal-conjectures into $FC_DIR"
  git clone "$FC_URL" "$FC_DIR"
fi

cd "$FC_DIR"
git fetch --tags --quiet origin
git checkout --quiet "$FC_REF"
say "Toolchain: $(cat lean-toolchain)"

say "Fetching prebuilt Mathlib cache"
lake exe cache get

say "Building project (sorry warnings are expected)"
lake build

mkdir -p Work
grep -qxF 'Work/' .git/info/exclude 2>/dev/null || echo 'Work/' >> .git/info/exclude

if command -v claude >/dev/null 2>&1; then
  if ! claude mcp list 2>/dev/null | grep -q '^lean-lsp'; then
    say "Registering lean-lsp MCP server with Claude Code"
    claude mcp add lean-lsp uvx lean-lsp-mcp
  fi
else
  say "Claude Code CLI not found; register later with: claude mcp add lean-lsp uvx lean-lsp-mcp"
fi

command -v rg >/dev/null 2>&1 || say "Optional: install ripgrep (rg) for lean_local_search"

say "Done. Run doctor.sh from $FC_DIR to verify."
