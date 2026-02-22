---
name: obsidian-padhy-review
description: Monthly vault review skill for Paddy's personal Obsidian vault. Activated by /padhy review keyword. Handles draft tag review, full tag audit, and vault optimization.
---

# obsidian_padhy_review — Padhy Vault Monthly Review

> Monthly review skill for Paddy's personal Obsidian vault (padhy).
> Companion to: [[obsidian_padhy]]

## When to activate
Activate when the user starts their message with `/padhy review`.

Do NOT activate for `/padhy` alone — that triggers the main vault workflow skill instead. Never trigger automatically.

---

## Purpose
The monthly review keeps your vault healthy over time. It has two parts:

1. **Draft tag review** — evaluate new tags added since the last review
2. **Full tag audit** — optimize the existing stable tag structure

The output is a review report note saved to `notes/` and an updated vault.

---

## Workflow

### Step 1 — Load the full tag picture (TWO tool calls)
- Call `list_files("tags")` to get all tag MOC files
- Read ALL tag MOC files — this is the one time you read broadly

Build a mental map of:
- Which tags are `status: draft` (new, unreviewed)
- Which tags are `status: stable` (reviewed)
- How many notes each tag connects to
- Which tags look similar, overlapping, or redundant

### Step 2 — Draft tag review
Present the user with all draft tags one by one (or grouped if there are many):

For each draft tag, suggest one of:
- **Keep as is** — good tag, promote to stable
- **Merge into [existing tag]** — too similar to an existing tag
- **Rename to [name]** — better name that matches how you talk
- **Delete** — too specific, noise, or only appears once

Wait for user confirmation before making any changes.

### Step 3 — Full tag audit
After draft review, look at ALL stable tags and surface:

- **Overlapping tags** — e.g. `finance` and `money` both exist, should they merge?
- **Thin tags** — tags with only 1-2 notes, should they be absorbed?
- **Naming inconsistencies** — e.g. `insurance` and `insurance-claims` — which is right?
- **Missing connections** — notes that probably should have a tag they're missing

Present findings as a list. Let the user decide what to act on.

### Step 4 — Make the changes
For each approved change:

- **Promote draft to stable**: Update the tag MOC frontmatter `status: draft` → `status: stable`
- **Merge tags**: Update all notes that use the old tag, move their backlinks to the new tag MOC, delete the old tag MOC
- **Rename tag**: Rename the MOC file, update frontmatter, update all backlinks
- **Delete tag**: Remove from all notes, delete the MOC file

Use `move_file` for renames. Use `read_file` + `complete_task` pattern for content updates.

### Step 5 — Write the review report
Call `complete_task` with:
- **title**: "Vault Review — [Month Year]" e.g. "Vault Review — February 2026"
- **summary**: What was reviewed, what changed, how many tags promoted/merged/deleted, any patterns noticed
- **tags**: `["vault-review"]`
- **attachments**: `[]`
- **next_steps**: Anything deferred for next review
- **move_files**: `{}` (no file moves in review)

---

## Tone During Review
Be direct and efficient. Present options clearly. Don't over-explain. The user knows their own vault — your job is to surface the decisions, not make them unilaterally.

Example format for presenting draft tags:

```
Draft tags to review (3):

1. **car** — 1 note (Car Insurance Claim Feb 2026)
   → Suggest: merge into `insurance` since the note is already tagged insurance
   
2. **freelance** — 2 notes (Invoice March, Tax Filing 2025)  
   → Suggest: keep, promote to stable

3. **medical-2026** — 1 note (Health Insurance Claim)
   → Suggest: rename to `medical`, too specific
```

---

## What NOT to do
- Do not make any changes without user confirmation
- Do not delete notes — only reorganize tags
- Do not add new tags during a review session
- Do not run the review automatically or mid-task