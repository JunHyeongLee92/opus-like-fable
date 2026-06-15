#!/usr/bin/env bash
# SessionStart hook: emit the Fable behavior spec as session context.
# Claude Code adds stdout (exit 0) of SessionStart hooks to the model's context.
# The hooks.json matcher includes "compact", so the spec survives compaction.
set -euo pipefail

SPEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../spec" && pwd)"
MODULES=(communication.md honesty.md autonomy.md delegation.md reporting.md memory.md)

echo "<fable-behavior-spec>"
echo "The following behavioral specification governs this entire session."
echo "Apply it to every turn. It complements (never overrides) safety policies."
for module in "${MODULES[@]}"; do
  echo ""
  cat "${SPEC_DIR}/${module}"
done
echo "</fable-behavior-spec>"

# Project memory index (spec/memory.md protocol): inject the table of contents
# so recall starts warm; bodies stay on disk.
MEMORY_INDEX="${CLAUDE_PROJECT_DIR:-}/.claude/fable-memory/MEMORY.md"
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -f "${MEMORY_INDEX}" ]; then
  echo ""
  echo "<fable-memory-index>"
  echo "Project memory index (one line per memory; read the file when relevant):"
  cat "${MEMORY_INDEX}"
  echo "</fable-memory-index>"
fi
