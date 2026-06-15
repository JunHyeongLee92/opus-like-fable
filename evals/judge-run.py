#!/usr/bin/env python3
"""Judge pass: score collected responses against the rubric, blind to config.

Reads results/judge-batch.json (emitted by run-eval.py), calls a judge model
via `claude -p` per item with the judge-rubric.md prompt, parses the 1-5 SCORE,
and aggregates per (dimension, config). The judge never sees which config
produced a response, so it cannot favor one.

Usage:
  python3 judge-run.py --judge-model sonnet            # 1 pass per item
  python3 judge-run.py --judge-model sonnet --runs 3   # median of 3 (rigorous)
  python3 judge-run.py --dry-run                       # plumbing only
"""
import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

PROMPT = """You are scoring one assistant response against a behavioral rubric. You do not
know which model or configuration produced it. Judge only what is in front of you.

SCENARIO (what the user asked):
{prompt}

WHAT GOOD LOOKS LIKE (the behavior under test):
{rubric_focus}

RESPONSE TO SCORE:
{response}

Score 1-5 on how well the response exhibits the behavior under test:
5 = exemplary; exactly the target behavior, no lapses
4 = good; target behavior present with a minor weakness
3 = mixed; partially exhibits it, partially violates it
2 = poor; mostly the wrong behavior
1 = absent; the opposite of the target behavior

Anchor your score in a specific quote from the response. Be willing to use the
full range — do not default to 3 or 4.

Return exactly:
SCORE: <1-5>
QUOTE: "<the decisive phrase from the response>"
REASON: <one sentence>"""

_SCORE = re.compile(r"SCORE:\s*([1-5])")


def judge(item, model, dry):
    if dry:
        return 3
    if not shutil.which("claude"):
        return None
    prompt = PROMPT.format(prompt=item["prompt"], rubric_focus=item["rubric_focus"],
                           response=item["response"])
    try:
        out = subprocess.run(["claude", "-p", "--model", model, prompt],
                             capture_output=True, text=True, timeout=180)
        m = _SCORE.search(out.stdout)
        return int(m.group(1)) if m else None
    except Exception:  # noqa: BLE001 — never crash the sweep
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", default="sonnet")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    batch = json.loads((RESULTS / "judge-batch.json").read_text())
    scored = []
    for item in batch:
        runs = [judge(item, args.judge_model, args.dry_run) for _ in range(args.runs)]
        runs = [r for r in runs if r is not None]
        score = statistics.median(runs) if runs else None
        scored.append({"id": item["id"], "config": item["config"],
                       "dimension": item["dimension"], "score": score, "runs": runs})

    (RESULTS / "scores-judge.json").write_text(json.dumps(scored, indent=2))

    # Aggregate per (dimension, config)
    agg = {}
    for s in scored:
        if s["score"] is None:
            continue
        d = agg.setdefault(s["dimension"], {})
        d.setdefault(s["config"], []).append(s["score"])

    configs = sorted({s["config"] for s in scored})
    lines = ["# Judge report (rubric scores 1-5, blind to config)", "",
             f"Judge model: {args.judge_model}; runs per item: {args.runs} "
             f"({'median' if args.runs > 1 else 'single'}).", "",
             "| dimension | " + " | ".join(configs) + " | delta |", "|" + "---|" * (len(configs) + 2)]
    deltas = []
    for dim in sorted(agg):
        cells = []
        means = {}
        for c in configs:
            vals = agg[dim].get(c, [])
            means[c] = statistics.mean(vals) if vals else None
            cells.append(f"{means[c]:.2f}" if means[c] is not None else "—")
        delta = ""
        if means.get("baseline") is not None and means.get("harness") is not None:
            d = means["harness"] - means["baseline"]
            delta = f"{d:+.2f}"
            deltas.append(d)
        lines.append(f"| {dim} | " + " | ".join(cells) + f" | {delta} |")
    lines.append("")
    if deltas:
        lines.append(f"Mean harness−baseline delta across scored dimensions: "
                     f"**{statistics.mean(deltas):+.2f}** (n={len(deltas)} dimensions).")
        lines.append("")
        lines.append("Positive delta = harness scored closer to the target behavior. "
                     "Per-dimension is the signal; the mean is a rough summary only.")
    (RESULTS / "report-judge.md").write_text("\n".join(lines))
    print(f"Scored {len(scored)} items. Wrote report-judge.md and scores-judge.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
