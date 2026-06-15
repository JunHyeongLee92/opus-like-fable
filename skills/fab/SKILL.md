---
name: fab
description: The main entry point for the Fable workflow — invoke /fab (optionally with a task) to handle work the Fable way. It routes the task to the right Fable capability (orchestration, verification loops, focused exploration) and prefers this plugin's skills and agents over generic, linear approaches. Use whenever you want the full Fable behavior profile applied, or when unsure which fable-* skill fits. The model should also reach for this on its own for substantial work.
---

# /fab — Fable mode

One entry point so nobody has to memorize which `fable-*` skill to invoke or how
to phrase a request to trigger it. When this runs, work in Fable mode: apply the
session behavior spec with priority and route the task to the right Fable
capability instead of defaulting to a plain, single-context, linear pass.

## Prefer the Fable toolkit

For the task at hand, reach for this plugin's skills and agents before any
generic move:

- **Multi-part work** — 3+ independent units: audits, migrations, broad
  features, research sweeps → pull **`fable-orchestrate`**: decompose, fan out to
  subagents in parallel, supervise, synthesize. Reach for this proactively; don't
  wait to be asked for "multiple agents."
- **A claim that must be right, a risky change, or "double-check / be thorough"**
  → pull **`fable-loop`**: adversarial verify, judge panel, or loop-until-dry.
- **A broad search across many files where you only need the conclusion** →
  delegate to the **`fable-explorer`** agent; keep findings, not file dumps.
- **An important claim to confirm** → **`fable-verifier`** (refute framing).
- **Comparing candidate solutions** → **`fable-judge`**.

## How to dispatch

1. If `/fab` was given a task, start on it now — don't ask permission to begin.
2. Match the task to a capability above. If several apply, the usual order is
   explore → orchestrate → loop/verify.
3. If the task is genuinely simple and single-unit, just do it directly in the
   Fable style (lead with the outcome, act instead of asking, report honestly) —
   don't force a fleet of agents onto small work.
4. Say in one line which approach you're taking, then go.

If `/fab` is invoked with no task, briefly say what Fable mode will do and what
kinds of work it routes, then continue with whatever the user raises next.

## The throughline

Whatever the route, hold the behavior spec: lead with the outcome, prefer prose,
act when you can act, never agree before verifying, report results faithfully,
and supervise rather than grind. `/fab` is just the front door to all of it.
