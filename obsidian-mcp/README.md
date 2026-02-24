# Sigil

MCP server for your Obsidian vault. Gives Claude structured access to your files, attachments, and knowledge structure via the Obsidian CLI.

## What it does

- **Reads any file** — markdown, PDF, images, Word, Excel, PowerPoint
- **Lists vault contents** — see what's in root or any folder
- **Moves files** — organizes attachments after tasks
- **Completes tasks** — writes summary notes, updates tag MOCs, archives daily note, moves files — all in one operation

## Prerequisites

1. **Obsidian 1.12+** with Catalyst license (early access)
2. **Obsidian CLI enabled**: Settings → General → Enable Command line interface
3. **Python 3.10+**
4. **uv** (installed by setup script if missing)

### Windows extra step
You need the `Obsidian.com` file from the `#insider-desktop-release` channel on the Obsidian Discord. Place it in the same folder as `Obsidian.exe`.

## Install as Claude Desktop extension

Download `sigil.mcpb` from the [latest release](https://github.com/notpaddy2k/sigil/releases) and install it in Claude Desktop.

## Manual setup

### macOS / Linux
```bash
chmod +x setup.sh
./setup.sh
```

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Then restart Claude Desktop.

## Install the skills

Copy the skills into your vault so they sync across machines:

```
your-vault/
  .claude/
    skills/
      obsidian.md          <- main task workflow skill
      obsidian-review.md   <- monthly review skill
```

## Vault structure expected

```
/vault-root
  2026-02-18.md        <- today's daily note + file drop zone
  new-file.pdf         <- drop new files here

/artifacts             <- organized attachments (subfoldered by topic)
/notes                 <- task summary notes
/tags                  <- tag MOC notes
/periodic/daily        <- archived daily notes
/templates             <- note templates
```

## Usage

**Starting a task:**
1. Drop any new files into your vault root
2. Open Claude Desktop
3. Describe what you need to do — "I need to file my taxes"
4. Claude finds relevant files, reads them, does the work
5. At the end, Claude calls `complete_task` — writes the note, organizes files, updates tags, archives the daily note

**Monthly review:**
- Say "monthly review" or "let's review my vault"
- Claude audits draft tags and stable tags
- You approve changes
- Claude writes a review report note

## Cross-machine setup

Store this repo (or just the `skills/` folder) in your vault on Google Drive. The MCP server itself needs to be installed on each machine (run setup script), but the skills travel with the vault automatically.
