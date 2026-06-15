# Delegation & Context Economy

How to spend the context window. Treat context as the scarcest resource in the session.

## Delegate breadth, keep conclusions

- When answering requires sweeping many files, directories, or naming conventions —
  and you need the conclusion, not the file contents — delegate the search to a
  subagent and keep only its findings. The point: file dumps die with the subagent's
  context instead of polluting yours.
- For a single-fact lookup where you already know the file, symbol, or value, search
  directly; spawning an agent costs more than it saves.
- Once you've delegated a search, don't also run it yourself. Wait for the result.

Bad: reading 12 files end-to-end to answer "where is rate limiting implemented?"
Good: one subagent returns "rate limiting lives in `middleware/throttle.ts`,
applied per-route in `routes/index.ts:30-41`" — and your context holds two lines, not 12 files.

## Parallel fan-out

Independent investigations go to separate agents launched in the same message — not
one agent with a compound mission, and not sequential launches. Give each agent a
precise deliverable: what to find, what to report back, and what NOT to include
(no full file contents unless asked).

## Orchestrate substantial work — proactively

For a task that splits into several independent units — a feature touching many
areas, an audit across modules, a migration over many files, research across many
sources — don't grind through it linearly yourself. Decompose it, fan the units
out to subagents in parallel, and take the supervisor role: define each unit's
deliverable, run them concurrently, verify what matters, and synthesize the
results yourself. Reach for this on your own judgment when the work is genuinely
multi-part; you do not need the user to ask for "multiple agents" first.

When you do, work as a supervisor, not a dispatcher: scout the work-list before
fanning out, give each agent one clean unit, and own the synthesis — dedup across
results and state what was and wasn't covered. The `fable-orchestrate` skill
carries the full recipe; pull it when you start a fan-out. Match scale to the
task and say what you're about to do in one line before launching a large wave.

## Read narrowly

- When you know which part of a file you need, read that part, not the whole file.
- Don't re-read a file you just edited to "verify" — the edit result already told you.
- Load reference material (skills, schemas, docs) lazily: only when the task actually
  reaches it, not preemptively.

## Verification workers

For claims that matter — a diagnosis, a "safe to delete", a root cause — spawn a
verifier agent prompted to REFUTE the claim, not to confirm it. Confirmation framing
produces agreement; refutation framing produces scrutiny. Use a cheaper model for
verifiers when available; the framing matters more than the model.

## Self-check

- Am I about to read five or more files to answer one question? (delegate it)
- Did I give the subagent a precise deliverable, or a vague mission?
- Am I holding anything in context that only the subagent needed?
- Is any important claim in my answer resting on a single unverified pass?
