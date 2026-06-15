<div align="center">

# opus-like-fable

**Run Claude Opus with a Fable-5-style behavior profile — a Claude Code plugin.**

![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-d97757)
![version](https://img.shields.io/badge/version-0.0.1-blue)
![license](https://img.shields.io/github/license/JunHyeongLee92/opus-like-fable)
![stars](https://img.shields.io/github/stars/JunHyeongLee92/opus-like-fable)

[English](README.md) · [한국어](README.ko.md)

</div>

Opus is already capable — what makes Fable *feel* different is how it behaves: it
leads with the outcome, acts instead of asking, pushes back instead of agreeing,
and finishes instead of promising. This plugin ports that behavior layer onto Opus
through an always-on spec, runtime hooks, and verification loops.

## Install

```sh
/plugin marketplace add JunHyeongLee92/opus-like-fable
/plugin install opus-like-fable@opus-like-fable
```

Use it on an Opus session (`/model opus`). Installed this way it stays on across
sessions. CLI works too: `claude plugin marketplace add …` then `claude plugin install …`.

## Usage

The behavior spec is always on once installed — nothing to invoke. When you want
it to take a task and pick the approach itself (fan out agents, verify, sweep the
codebase), there's one thing to remember:

```sh
/fab refactor the auth module and verify nothing broke
```

One entry point — you don't need to learn the individual skill names.

## What changes

| Typical Opus | With opus-like-fable |
|---|---|
| "You're absolutely right! Let me fix that." | Checks first; pushes back with evidence when you're wrong |
| "Should I update the tests?" | Updates them; asks only for risky or scope-changing calls |
| Ends with "Next, I'll refactor X" | A Stop hook blocks the turn — the refactor happens now |
| Reads 12 files to answer one question | Delegates the sweep, keeps a two-line conclusion |
| "Should work now!" (untested) | Runs it; reports the real result, failures included |
| Quietly runs `git push` mid-task | Irreversible commands escalate to a confirmation |

## What's included

| Type | Name | Role |
|---|---|---|
| Spec | 6 modules | always-on behavior — communication, honesty, autonomy, delegation, reporting, memory |
| Hook | SessionStart | injects the spec (survives compaction) |
| Hook | Stop | blocks ending a turn on unfinished work; lints format/tone |
| Hook | UserPromptSubmit | condition-triggered reminders |
| Hook | PreToolUse | guards `git push`/`commit`, `rm -rf`, package publishes |
| Skill | `/fab` | entry point that routes to the right capability |
| Skill | `fable-orchestrate`, `fable-loop` | multi-agent fan-out; verify / judge / loop-until-dry |
| Agent | `fable-verifier`, `fable-judge`, `fable-explorer` | refute-framed verify, rubric scoring, read-only sweeps |

<details>
<summary><strong>How it works</strong></summary>

Three injection channels mirror how Anthropic's own harness layers behavior —
always-on spec, conditional reminders, hard enforcement:

```
SessionStart  → injects the 6-module spec (~3k tokens); re-injected after compaction
UserPromptSubmit → format/tone violation in the last reply → targeted reminder;
                   otherwise a condensed spec every 12 turns
Stop          → lints every reply; BLOCKS turn-ending when the final paragraph is
                a promise of work instead of work (once per chain; offers exempt)
PreToolUse    → git push/commit, publishes, rm -rf, reset --hard → escalate to "ask"
                (never silent, never hard-denied — you stay in charge)
```

</details>

<details>
<summary><strong>Does it actually work? (measured)</strong></summary>

A blind eval (`evals/`) scored baseline Opus vs Opus+spec across 9 behavioral
dimensions (Opus 4.8):

- Improves where baseline slips: **delegation +1.0**, **autonomy +0.5**,
  **formatting +0.33** on a 1–5 rubric.
- The other six dimensions: Opus 4.8 already scores 5/5 — the plugin holds, it
  doesn't fake a gap.
- Formatting is weakest under spec-injection alone — exactly what the live
  Stop-hook lint targets, the clearest argument for the plugin over pasting the spec.

Honest framing: Opus 4.8 is already strong; the value is concentrated, not broad.
Full write-up in [`evals/findings-2way-baseline-harness.md`](evals/findings-2way-baseline-harness.md).

</details>

<details>
<summary><strong>What it is not</strong></summary>

- Not a jailbreak or identity cosplay — the model never claims to be Fable, and
  every guard *adds* friction to risky actions.
- Not a capability patch — it targets the interaction layer, which is most of
  what you feel.

</details>

## Requirements

bash and python3 (stdlib only). Hook state lives in `/tmp`; project memory in
`.claude/fable-memory/`.

## License & disclaimer

MIT — see [`LICENSE`](LICENSE). Unofficial community project, not affiliated with
or endorsed by Anthropic. "Claude", "Opus", "Fable", and "Anthropic" are
trademarks of Anthropic, used here only nominatively. Ships no Anthropic source or
system-prompt text; the behavior spec is an original paraphrase of publicly
observable behavioral patterns.
