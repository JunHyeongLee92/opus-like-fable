# Behavioral eval (P2)

Measures whether the plugin actually moves Opus toward Fable's behavior, per
dimension, instead of just feeling better. Three configs, scored blind.

## What it compares

| config | model | system prompt |
|---|---|---|
| `baseline` | Opus | stock |
| `harness` | Opus | + the 6 spec modules (via `--append-system-prompt`) |
| `fable` | Fable | stock |

The headline metric is **per-dimension proximity to Fable**:
`(harness − baseline) / (fable − baseline)`, clamped to [0,1]. Reported per
dimension, never blended — the point is to see what ports (formatting, autonomy,
sycophancy) and what doesn't (anything resting on reasoning depth).

## Honest scope

- This eval exercises the **spec injection**, the plugin's largest lever — not
  the live Stop/PreToolUse hooks, which need an interactive session (the
  deferred E2E milestone). So a high score here means "the spec works," and the
  hooks add enforcement on top of that, measured separately at E2E.
- Single-turn, no live tools. Dimensions that need real tool use (true
  delegation, multi-turn drift) are probed by description here and confirmed at
  E2E. `delegation-awareness` asks the model to *describe* its approach.
- Auto-scorers (`scorers.py`) cover only the objective, regex-detectable
  failures and are deliberately conservative. Everything else is the judge's.

## Run it

```bash
cd evals
python3 scorers.py --selftest          # verify the auto-scorers (14 cases)
python3 run-eval.py --dry-run          # verify plumbing, no model calls

# real run (needs the `claude` CLI on PATH):
python3 run-eval.py --models '{"opus":"opus","fable":"claude-fable-5"}'
# fable unavailable? compare the two you have:
python3 run-eval.py --configs baseline,harness
```

Outputs land in `results/`: `responses.json` (full records + auto-scores),
`judge-batch.json` (anonymized work items for the judge), `report-auto.md`
(deterministic pass-rates).

## Judge pass

`run-eval.py` does not call a judge model — it emits `judge-batch.json` so you
can score with any capable judge (the plugin's `fable-judge`, or an external
one). Follow `judge-rubric.md`: 1-5 per item, blind to config, median of 3,
quote-anchored. Merge the judge scores with the auto pass-rates into the
proximity table.

## Adding scenarios

One JSON object per line in `scenarios.jsonl`:
`id`, `dimension`, `prompt`, `auto_checks` (names from `scorers.CHECKS`),
`rubric_focus` (what good looks like, for the judge), `note`. Keep probes where
a baseline would plausibly slip and a Fable-like answer clearly wouldn't —
and include control cases (like `fmt-03`, where a list is correct) so the eval
can't be gamed by dogmatically suppressing structure.
