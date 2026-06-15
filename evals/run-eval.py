#!/usr/bin/env python3
"""3-way behavioral eval runner: baseline Opus vs Opus+harness vs Fable.

Design choices that matter:
- Model invocation goes through `claude -p` (headless print mode), so this runs
  wherever the Claude Code CLI is installed — no separate API key wiring.
  * baseline : claude -p --model <opus> "<prompt>"
  * harness  : claude -p --model <opus> --append-system-prompt "<spec>" "<prompt>"
  * fable    : claude -p --model <fable> "<prompt>"   (skipped if model absent)
- The harness condition approximates the plugin's SessionStart injection via
  --append-system-prompt. It does NOT exercise the Stop/PreToolUse hooks (those
  need a live interactive session — that's the deferred E2E milestone). So this
  eval measures the SPEC's effect, the largest single lever, not the full plugin.
- Auto-scorers run inline (deterministic). Judge scoring is emitted as a batch
  file for a separate judge pass, so this script has no model-judge dependency.

Usage:
  python3 run-eval.py --models '{"opus":"opus","fable":"claude-fable-5"}'
  python3 run-eval.py --dry-run        # no model calls; exercises plumbing
  python3 run-eval.py --configs baseline,harness   # skip fable if unavailable
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import scorers

ROOT = Path(__file__).resolve().parent
SPEC_DIR = ROOT.parent / "spec"
SPEC_MODULES = ["communication.md", "honesty.md", "autonomy.md",
                "delegation.md", "reporting.md", "memory.md"]
RESULTS = ROOT / "results"


def load_spec() -> str:
    parts = []
    for m in SPEC_MODULES:
        p = SPEC_DIR / m
        if p.exists():
            parts.append(p.read_text())
    return ("This behavioral specification governs every reply.\n\n"
            + "\n\n".join(parts))


def load_scenarios(filename="scenarios.jsonl"):
    with (ROOT / filename).open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run_claude(prompt, model, system, dry):
    if dry:
        return f"[dry-run response for model={model} system={'yes' if system else 'no'}]"
    if not shutil.which("claude"):
        return "[ERROR: `claude` CLI not on PATH]"
    cmd = ["claude", "-p", "--model", model]
    if system:
        cmd += ["--append-system-prompt", system]
    cmd.append(prompt)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return out.stdout.strip() or f"[empty output; stderr: {out.stderr.strip()[:200]}]"
    except subprocess.TimeoutExpired:
        return "[ERROR: timed out]"
    except Exception as exc:  # noqa: BLE001 — runner must never crash mid-sweep
        return f"[ERROR: {exc}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default='{"opus":"opus","fable":"claude-fable-5"}')
    ap.add_argument("--configs", default="baseline,harness,fable")
    ap.add_argument("--scenarios", default="scenarios.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    models = json.loads(args.models)
    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    spec = load_spec()
    scenarios = load_scenarios(args.scenarios)
    RESULTS.mkdir(exist_ok=True)

    plan = {
        "baseline": (models.get("opus", "opus"), None),
        "harness": (models.get("opus", "opus"), spec),
        "fable": (models.get("fable", "claude-fable-5"), None),
    }

    rows = []
    for sc in scenarios:
        for cfg in configs:
            if cfg not in plan:
                continue
            model, system = plan[cfg]
            resp = run_claude(sc["prompt"], model, system, args.dry_run)
            auto = scorers.score(resp, sc.get("auto_checks", []))
            rows.append({
                "id": sc["id"], "dimension": sc["dimension"], "config": cfg,
                "prompt": sc["prompt"], "rubric_focus": sc["rubric_focus"],
                "response": resp,
                "auto_scores": [{"check": n, "passed": p, "detail": d} for n, p, d in auto],
            })

    (RESULTS / "responses.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

    judge_items = [
        {"id": r["id"], "config": r["config"], "dimension": r["dimension"],
         "prompt": r["prompt"], "rubric_focus": r["rubric_focus"], "response": r["response"]}
        for r in rows
    ]
    (RESULTS / "judge-batch.json").write_text(json.dumps(judge_items, indent=2, ensure_ascii=False))

    write_auto_report(rows, configs)
    print(f"Wrote {len(rows)} responses, judge batch, and report-auto.md to {RESULTS}/")
    print("Next: run the judge pass over results/judge-batch.json (see judge-rubric.md), "
          "then merge scores into the proximity report.")
    return 0


def write_auto_report(rows, configs):
    by_dim = {}
    for r in rows:
        if not r["auto_scores"]:
            continue
        d = by_dim.setdefault(r["dimension"], {c: [0, 0] for c in configs})
        for a in r["auto_scores"]:
            d[r["config"]][1] += 1
            if a["passed"]:
                d[r["config"]][0] += 1

    lines = ["# Auto-scorer report (deterministic checks only)", "",
             "Pass-rate of regex auto-checks by dimension and config. Subjective",
             "dimensions are scored separately via the judge (see judge-rubric.md).", ""]
    if not by_dim:
        lines.append("_No auto-checked scenarios in this run._")
    for dim, cfgs in sorted(by_dim.items()):
        lines.append(f"## {dim}")
        for cfg in configs:
            done, total = cfgs.get(cfg, [0, 0])
            if total:
                lines.append(f"- {cfg}: {done}/{total} checks passed ({done / total:.0%})")
        lines.append("")
    (RESULTS / "report-auto.md").write_text("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
