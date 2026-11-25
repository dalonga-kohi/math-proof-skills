#!/usr/bin/env bash
# Launch one headless Claude Code session per agent in plan.json, in parallel.
# Usage: bash swarm_headless.sh Work/Erdos123/swarm [max_parallel]
#
# Each agent runs `claude -p` with its assignment as the prompt, its role's agent
# definition (if installed) appended as system prompt, and the model from plan.json.
# Output: <agent dir>/out.json (final result) and <agent dir>/log.txt.
#
# Permissions: headless runs cannot answer prompts. ALLOWED_TOOLS lists what each
# agent may do without asking; keep it narrow. Default: file edits, lake/python/
# solver commands, and the lean-lsp MCP tools.
set -euo pipefail

SWARM="${1:?usage: swarm_headless.sh <swarm dir> [max_parallel]}"
MAX="${2:-4}"
PLAN="$SWARM/plan.json"
ALLOWED_TOOLS="${ALLOWED_TOOLS:-Read Edit Write Glob Grep Bash(lake env lean:*) Bash(python3:*) Bash(kissat:*) Bash(cadical:*) mcp__lean-lsp}"
AGENT_DIRS="${AGENT_DIRS:-.claude/agents agents $HOME/.claude/agents}"

command -v claude >/dev/null || { echo "claude CLI not found"; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

mapfile -t ROWS < <(python3 -c '
import json, sys
for a in json.load(open(sys.argv[1]))["agents"]:
    print("\t".join([a["name"], a["agent_type"], a["model"], a["dir"], a["prompt_file"]]))
' "$PLAN")

run_one() {
  local name="$1" type="$2" model="$3" dir="$4" prompt_file="$5" sys_prompt=""
  for d in $AGENT_DIRS; do
    if [ -f "$d/$type.md" ]; then
      # body of the agent definition (strip YAML frontmatter)
      sys_prompt="$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$d/$type.md")"
      break
    fi
  done
  echo "[start] $name ($model)"
  claude -p "$(cat "$prompt_file")" \
      --model "$model" \
      ${sys_prompt:+--append-system-prompt "$sys_prompt"} \
      --allowedTools "$ALLOWED_TOOLS" \
      --output-format json > "$dir/out.json" 2> "$dir/log.txt" \
    && echo "[done]  $name" || echo "[fail]  $name (see $dir/log.txt)"
}

running=0
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r name type model dir prompt_file <<< "$row"
  run_one "$name" "$type" "$model" "$dir" "$prompt_file" &
  running=$((running+1))
  if [ "$running" -ge "$MAX" ]; then wait -n; running=$((running-1)); fi
done
wait
echo "All agents finished. Merge reports from $SWARM/*/out.json into ledger.jsonl and blackboard.md."
