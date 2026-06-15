#!/usr/bin/env python3
"""Stop hook: enforce the last-paragraph check from spec/autonomy.md.

If the assistant's final message ends on a promise of future work or a
permission-seeking question, block the stop once and quote the rule back.
Enforcement ladder: we block at most once per stop attempt chain
(stop_hook_active == True -> always allow), so a genuinely blocked turn can
still end on the second pass. Claude Code itself caps consecutive blocks at 8.
"""
import json
import re
import sys
from pathlib import Path

TAIL_CHARS = 600  # hard cap on how much of the ending we inspect

# Promises of future work / permission-seeking endings. English + Korean.
PROMISE_PATTERNS = [
    r"\bI[' ]?ll\s+\w+",
    r"\bI\s+will\s+(?:now\s+)?\w+",
    r"\bI'?m\s+going\s+to\s+\w+",
    r"\bLet\s+me\s+(?:now\s+)?\w+",
    r"\bNext,?\s+I(?:'ll| will)\b",
    r"\bShall\s+I\b",
    r"\bWant\s+me\s+to\b",
    r"\bWould\s+you\s+like\s+me\s+to\b",
    r"(?:하겠습니다|할게요|해보겠습니다|진행하겠습니다|작성하겠습니다|시작하겠습니다)\s*\.?\s*$",
    r"(?:해\s*드릴까요|할까요|진행할까요|시작할까요)\s*\?\s*$",
]
COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in PROMISE_PATTERNS]

# Endings that legitimately wait on the user: don't block these.
BLOCKED_ON_USER = re.compile(
    r"(blocked on|need(?:s)? your|waiting for your|어느 쪽|선택해|결정해|알려주(?:세요|시면))",
    re.IGNORECASE,
)

# Follow-up OFFERS after finished work are allowed by the spec ("offering
# follow-ups after the task is done is fine"). A sentence is an offer, not a
# promise, when it's conditional or invitational.
OFFER_EXEMPT = re.compile(
    r"(\bif you\b|\bgladly\b|\bhappy to\b|\blet me know\b|\bfeel free\b"
    r"|필요하(?:면|시면)|원하시면|언제든)",
    re.IGNORECASE,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n")

REASON = (
    "Your final paragraph promises or proposes work instead of doing it. "
    "Per the session behavior spec (autonomy: last-paragraph check), the turn "
    "is not done: carry out that work now with tool calls. If you are genuinely "
    "blocked on input only the user can provide, restate plainly what you need "
    "and why you cannot proceed without it."
)

FENCE = re.compile(r"```.*?```", re.S)
SYCOPHANT_OPENER = re.compile(
    r"^\s*((you'?re|you are) (absolutely |completely |totally )?right\b"
    r"|great (question|point|idea|catch)\b"
    r"|excellent (question|point|idea)\b|what a great\b|perfect!\s)",
    re.IGNORECASE,
)
HEADER_LINE = re.compile(r"^#{1,3}\s", re.M)
BULLET_LINE = re.compile(r"^\s*[-*•]\s")


def lint_format(text: str) -> list:
    """Detect formatting/tone violations of the behavior spec in prose.

    Conservative on purpose: a reminder that fires on borderline cases trains
    the model to ignore reminders. Code fences are exempt entirely.
    """
    prose = FENCE.sub("", text)
    violations = []
    if SYCOPHANT_OPENER.search(prose.strip()):
        violations.append("sycophantic opener (agreeing/praising before verifying)")
    if prose.count("→") >= 2:
        violations.append("arrow-chain shorthand in prose")
    lines = [line for line in prose.splitlines() if line.strip()]
    if len(lines) >= 8:
        bullets = [line for line in lines if BULLET_LINE.match(line)]
        if len(bullets) / len(lines) > 0.6:
            violations.append("bullet-dominated response where prose was expected")
    if len(prose.strip()) < 400 and HEADER_LINE.search(prose):
        violations.append("section headers on a short answer")
    return violations


def last_assistant_text(transcript_path: str) -> str:
    path = Path(transcript_path)
    if not path.exists():
        return ""
    text = ""
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                content = (entry.get("message") or {}).get("content") or []
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if parts:
                    text = "\n".join(parts)
    except OSError:
        return ""
    return text


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    full_text = last_assistant_text(str(payload.get("transcript_path", "")))
    if not full_text:
        return

    # Format lint runs on every stop (never blocks): violations are flagged for
    # reminder.py to inject a targeted reminder on the next user turn. This is
    # the condition-triggered channel, mirroring claude.ai's anthropic_reminders.
    violations = lint_format(full_text)
    session_id = str(payload.get("session_id", "unknown"))[:64]
    lint_file = Path(f"/tmp/opus-like-fable-{session_id}.lint")
    try:
        if violations:
            lint_file.write_text(json.dumps(violations))
        elif lint_file.exists():
            lint_file.unlink()
    except OSError:
        pass

    if payload.get("stop_hook_active"):
        return  # already blocked once this chain; let the turn end
    # Only the LAST paragraph can convict the turn: the spec explicitly allows
    # offering follow-ups after finished work, so an "I'll…" mid-message is fine.
    tail = full_text.strip().split("\n\n")[-1][-TAIL_CHARS:]
    if BLOCKED_ON_USER.search(tail):
        return
    for sentence in SENTENCE_SPLIT.split(tail):
        if not sentence.strip() or OFFER_EXEMPT.search(sentence):
            continue
        if any(p.search(sentence) for p in COMPILED):
            print(json.dumps({"decision": "block", "reason": REASON}))
            return


if __name__ == "__main__":
    main()
