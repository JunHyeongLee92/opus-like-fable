#!/usr/bin/env python3
"""PreToolUse hook (Bash): escalate irreversible / outward-facing commands.

Enforces spec/reporting.md "before destructive or outward-facing actions" at
the harness level. We cannot know from here whether the user explicitly asked,
so the decision is "ask" (escalate to the permission prompt), never "deny":
the user stays the authority, the model just can't slip these through quietly.
"""
import json
import re
import sys

GUARDED = [
    (r"\bgit\s+push\b", "git push publishes commits outside the session"),
    (r"\bgit\s+commit\b", "commits require an explicit user request"),
    (r"\bgh\s+(pr\s+create|release\s+create)\b", "creates outward-facing GitHub objects"),
    (r"\bnpm\s+publish\b|\bcargo\s+publish\b|\btwine\s+upload\b", "publishes a package"),
    (r"\bcurl\b[^|;&]*(-X\s*(POST|PUT|DELETE|PATCH)|--data|-d\s)", "outbound write request"),
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "recursive force delete"),
    (r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-zA-Z]*f", "discards local work"),
]
COMPILED = [(re.compile(p, re.IGNORECASE), why) for p, why in GUARDED]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    if payload.get("tool_name") != "Bash":
        return
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if not command:
        return

    for pattern, why in COMPILED:
        if pattern.search(command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        f"Guarded by opus-like-fable ({why}). Confirm this was "
                        "explicitly requested by the user in this session."
                    ),
                }
            }))
            return


if __name__ == "__main__":
    main()
