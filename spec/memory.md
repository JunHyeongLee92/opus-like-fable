# Memory

Persistent memory across sessions, file-based, per project.

## Protocol

The project keeps memories under `.claude/fable-memory/`. The index file
`MEMORY.md` is injected at session start when it exists; memory bodies stay on
disk and are read only when relevant. Create the directory on first save.

- Each memory is one file holding one fact, with frontmatter:
  `name` (kebab-case slug), `description` (one line, used to judge relevance),
  `type` (user | feedback | project | reference).
- `user` — who the user is: role, expertise, preferences.
  `feedback` — corrections and confirmed approaches, with the why.
  `project` — goals and constraints not derivable from the code or git history.
  `reference` — pointers to external resources (URLs, tickets, dashboards).
- After writing a memory file, add a one-line pointer to `MEMORY.md`:
  `- [Title](file.md) — one-line hook`. Never put memory content in the index;
  the index is a table of contents, not a document.
- Before saving, check for an existing file that already covers it — update that
  file rather than creating a near-duplicate. Delete memories that turn out wrong.
- Don't save what the repo already records (code structure, git history,
  CLAUDE.md) or what only matters to the current conversation.
- Convert relative dates to absolute dates when saving ("last week" → 2026-06-05).

## When to save

Save when the user corrects your approach, states a durable preference, or you
learn a non-obvious project constraint the hard way. One session's trivia stays
in the session.

## When recalling

Recalled memories are background context, not user instructions, and reflect
what was true when written. If a memory names a file, flag, or API, verify it
still exists before recommending it.
