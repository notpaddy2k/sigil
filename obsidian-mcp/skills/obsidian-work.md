---
name: obsidian-work
description: Vault workflow skill for Paddy's work Obsidian vault. Activated by /work keyword. Handles task execution, file reading, note creation, tag management, and vault organization.
---

# obsidian-work — Work Vault Skill

---

## When to activate
Activate when the user starts their message with `/work`.

Do NOT activate for any message that does not begin with `/work`. Ignore all vault tools and workflow for those messages entirely.

---

## Vault Root

**Mac:**
```
/Users/preritp/Library/CloudStorage/OneDrive-iSeyonAnalytics/work/
```

**Windows:**
```
C:\Users\PreritPadhy\OneDrive - iSeyon Analytics\work\
```

Daily note pattern: `<vault-root>YYYY-MM-DD.md`

**Important:** `read_file` accepts relative paths from vault root — the MCP server resolves the vault root automatically.

---

## Vault Structure

```
/vault-root
  2026-02-18.md        ← today's daily note + drop zone for new files

/artifacts             ← organized attachments, subfoldered by project/client
  /vuori/
  /iseyon/
  /clients/
  ...

/notes                 ← task summary notes
/tags                  ← tag MOC notes
/periodic/daily        ← archived daily notes
/templates             ← note templates (do not modify during tasks)
```

---

## Workflow

### Step 1 — Read today's daily note immediately
As soon as `/work` is triggered, call `read_file("YYYY-MM-DD.md")` with today's date before doing anything else. This gives you full context of what the user is working on. Do not ask clarifying questions before doing this.

### Step 2 — Understand the task
From the daily note and the user's message, understand what needs to be done. Ask one clarifying question only if truly necessary — otherwise proceed directly.

### Step 3 — Read what you need
Call `read_file` with relative paths from vault root e.g. `read_file("artifacts/vuori/forecast-brief.pdf")`. The MCP resolves the vault root automatically. Only read files directly relevant to the task.

### Step 4 — Do the work
Work through the task with the user. Draft, summarize, calculate, extract — whatever the task requires.

### Step 5 — Complete the task (ONE call)
When done, call `complete_task` from the MCP. This handles everything atomically:
1. Writes summary note → `notes/`
2. Creates/updates tag MOCs → `tags/`
3. Moves files from root → `artifacts/`
4. Archives daily note → `periodic/daily/`

Feed it:
- **title** — clear and descriptive e.g. "Vuori Forecast Accuracy Framework"
- **summary** — what was done, key decisions, technical details, next steps. Write as if briefing a colleague.
- **tags** — derived from how the user described the task (see Tag Rules)
- **attachments** — full vault paths of all files used
- **next_steps** — concrete actionable items only, empty if none
- **move_files** — map of `{source: destination}` for organizing files

---

## Tag Rules

**Always prefer existing tags.** Check what MOC files exist in `tags/` before creating anything new. Use those exact names.

**Derive tags from the user's own words.** If they said "Vuori forecast" → `forecasting`, `vuori`. If they said "Iseyon client proposal" → `iseyon`, `consulting`. Do not normalize or impose structure.

**New tags get `status: draft` automatically** — `complete_task` handles this.

**Keep tags broad.** Prefer `forecasting` over `vuori-demand-forecast-2026`. Specificity lives in the note.

**2-4 tags per note maximum.**

---

## What NOT to do
- Do not read files speculatively — only what's needed
- Do not create overly specific tags
- Do not make multiple separate write calls — always use `complete_task` for the final step
- Do not archive the daily note if the user says they're not done for the day
- Do not ask the user to organize files — Claude handles that in `complete_task`
