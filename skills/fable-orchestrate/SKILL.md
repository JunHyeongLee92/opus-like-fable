---
name: fable-orchestrate
description: Multi-agent orchestration for parallelizable work - codebase audits, migrations, broad reviews, research sweeps, feature work touching many areas. Use PROACTIVELY whenever a task decomposes into roughly 3+ independent units, without waiting for the user to ask for "multiple agents" - reach for it on your own judgment. Plans the fan-out, runs agents in parallel waves, synthesizes coverage-audited results.
---

# Fable orchestration

Structured fan-out for work one context can't hold. The discipline below is what
separates orchestration from spawning a pile of agents.

## Proactive, with cost discipline

Default to orchestrating multi-part work yourself — you don't need the user to
ask for it. The judgment is about scale, not permission:

- Genuinely multi-part (roughly 3+ independent units): fan out and supervise.
- Trivial or single-unit work: just do it inline; a fleet for a one-file change
  wastes tokens and your own context.
- Before launching a large wave (more than ~4 agents), say what you're about to
  do in one line ("fanning out 8 agents over the module list") so the user can
  redirect if the scale is wrong. Announce — don't ask for permission.

This is deliberately more proactive than stock behavior: orchestrate on your own
judgment, and let the announce-before-large-wave step be the safety valve.

## The shape of a wave

1. **Scout inline first.** Discover the work-list yourself (file list, module
   map, finding categories) with cheap direct searches. You need the list before
   the fan-out, not a guess.
2. **Decompose into independent units.** Each agent gets exactly one unit and a
   precise deliverable: what to find, the report format (short prose +
   `file:line` references), and what NOT to include (no file dumps).
3. **Launch each wave in ONE message** - all independent agents as parallel tool
   calls. Sequential launches waste the whole point.
4. **Don't barrier without need.** Move each unit forward as its result arrives.
   Wait for the full wave only when the next step genuinely needs cross-unit
   context (dedup across findings, "zero findings -> skip verification").
5. **Verify what matters.** Route important findings through `fable-verifier`
   (refute framing) before they reach the synthesis - plausible-but-wrong
   findings are the failure mode of fan-out.

## Synthesis discipline

- Deduplicate findings against everything seen, not just the last wave.
- The final report names its coverage: which units were swept, by which angles,
  and what was NOT covered. Silent truncation reads as "covered everything".
- If any unit's agent failed or returned garbage, say so and either re-run it or
  list it as a gap - never paper over a hole in the sweep.

## Scale guidance

"Find any issues" - 3-5 agents, single-pass. "Audit this thoroughly" - full
work-list coverage plus a verification pass plus a completeness critic: one
final agent asked "what's missing - which unit, angle, or claim went unchecked?"
whose answer becomes the next wave if non-empty.
