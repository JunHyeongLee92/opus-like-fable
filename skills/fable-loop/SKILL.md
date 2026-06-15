---
name: fable-loop
description: Capability-compensation loop recipes for high-stakes work. Use when a task needs more assurance than one pass gives - verifying an important diagnosis or risky change (two-phase verify), choosing between solution approaches (judge panel), or exhaustively finding issues like bugs or dead code (loop-until-dry). Also use when the user asks to "double-check", "be thorough", or "make sure".
---

# Fable loops

Three loop recipes that buy back, with structure, what a single pass can miss.
All three use the plugin agents: `fable-verifier` (haiku, refute framing),
`fable-judge` (rubric scoring), `fable-explorer` (read-only search).

## 1. Two-phase verify - for important claims and risky changes

Use for: a root-cause diagnosis, "safe to delete", "this migration is correct",
any claim the user will act on.

1. Finish the work and form the claim with its evidence.
2. Spawn `fable-verifier` with the claim AND the evidence, phrased to refute.
   For critical claims spawn 2-3 verifiers in parallel, each with a different
   lens (correctness / side effects / does-it-reproduce).
3. `REFUTED` -> treat the refutation as new work; fix and re-verify.
   `COULD-NOT-REFUTE` from the majority -> report to the user, citing what was
   checked. Never skip from "verifier disagreed" straight to reporting success.

## 2. Judge panel - for wide solution spaces

Use for: design choices, refactoring strategies, anything where the first idea
anchors too hard.

1. Produce 2-3 genuinely different candidates (different angles: minimal-diff,
   long-term-structure, performance-first - not three drafts of one idea).
2. Spawn `fable-judge` with all candidates, the task, and 3-4 rubric dimensions.
3. Take the winner; graft any clearly better idea from the runners-up. Tell the
   user which candidate won and the decisive reason.

## 3. Loop-until-dry - for unknown-size discovery

Use for: "find all the bugs / unused code / inconsistencies" - anywhere a count
target would silently miss the tail.

1. Spawn `fable-explorer` (or several, one search angle each: by-name,
   by-content, by-caller) and collect findings.
2. Deduplicate against everything already seen, not just last round.
3. Repeat with fresh angles until 2 consecutive rounds find nothing new.
4. Report the total AND the angles searched, so coverage is auditable.

## Scope discipline

These loops cost tokens. Match depth to stakes: one verifier for a routine
claim, a panel only when the user signalled thoroughness or the blast radius is
large. Always tell the user which loop ran and what it changed - a loop that
silently "made things better" violates the reporting spec.
