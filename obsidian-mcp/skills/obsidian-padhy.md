---
name: obsidian-padhy
description: Vault workflow skill for Paddy's personal Obsidian vault. Activated by /padhy keyword. Handles task execution, file reading, note creation, tag management, and vault organization.
---

# obsidian_padhy — Padhy Vault Skill

> Vault workflow skill for Paddy's personal Obsidian vault (padhy).
> For CLI syntax reference see: obsidian-cli.md in vault root.

---

## When to activate
Activate when the user starts their message with `/padhy`.

Do NOT activate for any message that does not begin with `/padhy`. Ignore all vault tools and workflow for those messages entirely.

---

## Vault Root

**Windows:**
```
G:\My Drive\Obsidian\padhy\
```

**Mac:**
```
/Users/preritp/Library/CloudStorage/GoogleDrive-paddynco2k@gmail.com/My Drive/Obsidian/padhy/
```

Daily note pattern: `<vault-root>YYYY-MM-DD.md`

**Important:** `read_file` accepts relative paths from vault root — no need for full absolute paths. The MCP server resolves the vault root automatically.

## Vault Structure

```
G:\My Drive\Obsidian\padhy\
  2026-02-18.md        ← today's daily note + drop zone for new files
  new-doc.pdf          ← new files dropped here

  artifacts/           ← organized attachments, subfoldered by topic
    taxes/
    insurance/
    finance/
    ...

  notes/               ← task summary notes
  tags/                ← tag MOC notes
  periodic/daily/      ← archived daily notes
  templates/           ← note templates (do not modify during tasks)
```

---

## Workflow

### Step 1 — Read today's daily note immediately
As soon as `/padhy` is triggered, call `read_file("YYYY-MM-DD.md")` with today's date before doing anything else. This gives you full context of what the user is working on. Do not ask clarifying questions before doing this.

### Step 2 — Understand the task
From the daily note and the user's message, understand what needs to be done. Ask one clarifying question only if truly necessary — otherwise proceed directly.

### Step 3 — Read what you need
Call `read_file` with relative paths from vault root e.g. `read_file("artifacts/taxes/w2.pdf")`. The MCP resolves the vault root automatically on both Mac and Windows. Only read files directly relevant to the task.

### Step 4 — Do the work
Work through the task with the user. Draft, summarize, calculate, extract — whatever the task requires.

### Step 5 — Complete the task (ONE call)
When done, call `complete_task` from the MCP. This handles everything atomically:
1. Writes summary note → `notes/`
2. Creates/updates tag MOCs → `tags/`
3. Moves files from root → `artifacts/`
4. Archives daily note → `periodic/daily/`

Feed it:
- **title** — clear and descriptive e.g. "Tax Filing 2025"
- **summary** — what was done, key facts, dates, reference numbers, decisions. Write as if leaving a note to read in 6 months.
- **tags** — derived from how the user described the task (see Tag Rules)
- **attachments** — full vault paths of all files used e.g. `artifacts/taxes/w2-2025.pdf`
- **next_steps** — concrete actionable items only, empty if none
- **move_files** — map of `{source: destination}` for organizing files e.g. `{"w2.pdf": "artifacts/taxes/w2.pdf"}`

---

## Tag Rules

**Always prefer existing tags.** Before picking tags, check what MOC files exist:
```bash
obsidian files folder=tags
```
Use those exact names before creating anything new.

**Derive tags from the user's own words.** If they said "filing my taxes" → `taxes`. If they said "car insurance claim" → `["insurance", "car"]`. Do not normalize, singularize, or impose structure.

**New tags get `status: draft` automatically** — `complete_task` handles this. Any tag without an existing MOC is created as draft for the monthly review.

**Keep tags broad.** Prefer `taxes` over `federal-taxes-2025`. Specificity lives in the note, not the tag.

**2-4 tags per note maximum.**

---

## Summary Note Frontmatter

```yaml
---
date: 2026-02-18
tags: [taxes, finance]
status: complete
attachments: [[w2-2025]]
---
```

---

## What NOT to do
- Do not read files speculatively — only what's needed
- Do not create overly specific tags
- Do not make multiple separate write calls — always use `complete_task` for the final step
- Do not archive the daily note if the user says they're not done for the day
- Do not ask the user to organize files — Claude handles that in `complete_task`
- Do not call `obsidian files` more than once unless the user references a new subfolder