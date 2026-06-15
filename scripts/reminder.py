#!/usr/bin/env python3
"""UserPromptSubmit hook: sparse long-conversation reminder.

Mirrors claude.ai's long_conversation_reminder. Injected rarely on purpose:
a reminder every turn stops being a reminder (guardrail pattern: scarcity
preserves salience). State is one integer per session under /tmp.
"""
import json
import sys
from pathlib import Path

REMIND_EVERY = 12  # turns between reminders; first reminder at turn 12

CONDENSED_SPEC = """<fable-behavior-reminder>
Long-conversation reminder of the session behavior spec (full text was injected
at session start):
- Lead with the outcome; write complete prose for a teammate catching up.
  No arrow chains, fragments, or invented labels. Minimal formatting.
- Never agree or praise before verifying ("You're absolutely right" is banned);
  push back with evidence when the user is wrong; own mistakes without groveling.
- Act when you can act. Don't ask permission for reversible steps; don't end
  the turn on a plan or promise — do that work now. Stop only when done or
  genuinely blocked on the user.
- Delegate broad searches; keep conclusions, not file dumps. Parallelize
  independent calls.
- Report faithfully: failures with output, skipped steps named, no unverified
  "done", no hedged success. Verify destructive targets before touching them.
</fable-behavior-reminder>"""

LINT_TEMPLATE = """<fable-format-reminder>
Your previous reply violated the session behavior spec: {issues}.
Re-read the communication and honesty rules: default to prose, no arrow-chain
shorthand, no sycophantic openers, structure only when the content demands it.
Apply them to this reply.
</fable-format-reminder>"""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # malformed input: stay silent, never break the session

    session_id = str(payload.get("session_id", "unknown"))[:64]

    # Condition-triggered reminder: stop-check.py flags format violations of the
    # previous assistant message; we deliver the targeted reminder exactly once.
    lint_file = Path(f"/tmp/opus-like-fable-{session_id}.lint")
    if lint_file.exists():
        try:
            issues = ", ".join(json.loads(lint_file.read_text()))
            lint_file.unlink()
            if issues:
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": LINT_TEMPLATE.format(issues=issues),
                    }
                }))
                return  # one reminder per turn; periodic one can wait
        except (OSError, ValueError):
            pass

    state_file = Path(f"/tmp/opus-like-fable-{session_id}.count")

    try:
        count = int(state_file.read_text().strip()) if state_file.exists() else 0
    except (ValueError, OSError):
        count = 0
    count += 1
    try:
        state_file.write_text(str(count))
    except OSError:
        pass  # state loss degrades to "no reminder", which is safe

    if count % REMIND_EVERY == 0:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": CONDENSED_SPEC,
            }
        }))


if __name__ == "__main__":
    main()
