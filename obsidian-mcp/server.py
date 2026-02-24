"""
Sigil for Obsidian — MCP Server
Exposes every non-developer Obsidian CLI command as an MCP tool.
Server only changes if Obsidian CLI changes. Workflow logic lives in skills.
"""

import re
import subprocess
import shutil
import platform
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sigil")


# ── Core CLI runner ───────────────────────────────────────────────────────────

def run(cmd: list[str]) -> str:
    """Run an obsidian CLI command and return clean stdout."""
    binary = shutil.which("obsidian")
    if not binary:
        if platform.system() == "Darwin":
            binary = "/Applications/Obsidian.app/Contents/MacOS/Obsidian"
        elif platform.system() == "Windows":
            binary = shutil.which("obsidian.exe") or "obsidian"
        else:
            binary = "obsidian"

    result = subprocess.run(
        [binary] + cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Filter Obsidian log lines (e.g. "2026-02-19 18:13:10 Loading updated app package...")
    lines = result.stdout.splitlines()
    clean = "\n".join(l for l in lines if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ', l))

    if result.returncode != 0:
        err = result.stderr.strip() or clean.strip()
        raise RuntimeError(f"Obsidian CLI error: {err}")

    return clean.strip()


def vault_prefix(vault: str = "") -> list[str]:
    """Return vault targeting prefix if specified.
    Quotes the vault name only if it contains spaces, e.g.:
        vault=padhy        (no spaces)
        vault="My Vault"   (has spaces)
    """
    if not vault:
        return []
    v = f'"{vault}"' if " " in vault else vault
    return [f"vault={v}"]


def arg(key: str, value: str) -> str:
    """Format a key=value CLI argument.
    No shell quoting needed — subprocess list mode passes args natively."""
    return f"{key}={value}"


# ── General ───────────────────────────────────────────────────────────────────

@mcp.tool()
def obsidian_help() -> str:
    """Show list of all available Obsidian CLI commands."""
    return run(["help"])


@mcp.tool()
def obsidian_version() -> str:
    """Show Obsidian version."""
    return run(["version"])


# ── Daily notes ───────────────────────────────────────────────────────────────

@mcp.tool()
def daily_read(vault: str = "") -> str:
    """Read today's daily note contents.

    Args:
        vault: Target vault name (optional, defaults to active vault)
    """
    return run(vault_prefix(vault) + ["daily:read"])


@mcp.tool()
def daily_open(pane_type: str = "", silent: bool = False, vault: str = "") -> str:
    """Open today's daily note.

    Args:
        pane_type: tab|split|window
        silent: Return path without opening
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["daily"]
    if pane_type:
        args.append(f"paneType={pane_type}")
    if silent:
        args.append("silent")
    return run(args)


@mcp.tool()
def daily_append(content: str, pane_type: str = "", inline: bool = False, silent: bool = False, vault: str = "") -> str:
    """Append content to today's daily note.

    Args:
        content: Content to append (required)
        pane_type: tab|split|window
        inline: Append without newline
        silent: Do not open file
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["daily:append", arg("content", content)]
    if pane_type:
        args.append(f"paneType={pane_type}")
    if inline:
        args.append("inline")
    if silent:
        args.append("silent")
    return run(args)


@mcp.tool()
def daily_prepend(content: str, pane_type: str = "", inline: bool = False, silent: bool = False, vault: str = "") -> str:
    """Prepend content to today's daily note.

    Args:
        content: Content to prepend (required)
        pane_type: tab|split|window
        inline: Prepend without newline
        silent: Do not open file
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["daily:prepend", arg("content", content)]
    if pane_type:
        args.append(f"paneType={pane_type}")
    if inline:
        args.append("inline")
    if silent:
        args.append("silent")
    return run(args)


# ── Files and folders ─────────────────────────────────────────────────────────

@mcp.tool()
def file_info(file: str = "", path: str = "", vault: str = "") -> str:
    """Show file info.

    Args:
        file: File name (wikilink resolution)
        path: Exact path from vault root
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["file"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def files_list(folder: str = "", ext: str = "", total: bool = False, vault: str = "") -> str:
    """List files in the vault.

    Args:
        folder: Filter by folder path
        ext: Filter by extension (e.g. md, pdf)
        total: Return file count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["files"]
    if folder:
        args.append(arg("folder", folder))
    if ext:
        args.append(f"ext={ext}")
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def folder_info(path: str, info: str = "", vault: str = "") -> str:
    """Show folder info.

    Args:
        path: Folder path (required)
        info: files|folders|size — return specific info only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["folder", arg("path", path)]
    if info:
        args.append(f"info={info}")
    return run(args)


@mcp.tool()
def folders_list(folder: str = "", total: bool = False, vault: str = "") -> str:
    """List folders in the vault.

    Args:
        folder: Filter by parent folder
        total: Return folder count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["folders"]
    if folder:
        args.append(arg("folder", folder))
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def file_open(file: str = "", path: str = "", newtab: bool = False, vault: str = "") -> str:
    """Open a file in Obsidian.

    Args:
        file: File name
        path: Exact path from vault root
        newtab: Open in new tab
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["open"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if newtab:
        args.append("newtab")
    return run(args)


@mcp.tool()
def file_create(name: str = "", path: str = "", content: str = "", template: str = "", overwrite: bool = False, silent: bool = False, newtab: bool = False, vault: str = "") -> str:
    """Create or overwrite a file.

    Args:
        name: File name
        path: File path from vault root
        content: Initial content
        template: Template to use
        overwrite: Overwrite if file exists
        silent: Create without opening
        newtab: Open in new tab
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["create"]
    if name:
        args.append(arg("name", name))
    if path:
        args.append(arg("path", path))
    if content:
        args.append(arg("content", content))
    if template:
        args.append(arg("template", template))
    if overwrite:
        args.append("overwrite")
    if silent:
        args.append("silent")
    if newtab:
        args.append("newtab")
    return run(args)


@mcp.tool()
def file_read(file: str = "", path: str = "", vault: str = "") -> str:
    """Read file contents.

    Args:
        file: File name (wikilink resolution)
        path: Exact path from vault root
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["read"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def file_append(content: str, file: str = "", path: str = "", inline: bool = False, vault: str = "") -> str:
    """Append content to a file.

    Args:
        content: Content to append (required)
        file: File name
        path: Exact path from vault root
        inline: Append without newline
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["append", arg("content", content)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if inline:
        args.append("inline")
    return run(args)


@mcp.tool()
def file_prepend(content: str, file: str = "", path: str = "", inline: bool = False, vault: str = "") -> str:
    """Prepend content after frontmatter of a file.

    Args:
        content: Content to prepend (required)
        file: File name
        path: Exact path from vault root
        inline: Prepend without newline
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["prepend", arg("content", content)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if inline:
        args.append("inline")
    return run(args)


@mcp.tool()
def file_move(to: str, file: str = "", path: str = "", vault: str = "") -> str:
    """Move or rename a file.

    Args:
        to: Destination folder or path (required)
        file: File name
        path: Exact path from vault root
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["move", arg("to", to)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def file_delete(file: str = "", path: str = "", permanent: bool = False, vault: str = "") -> str:
    """Delete a file (moves to trash by default).

    Args:
        file: File name
        path: Exact path from vault root
        permanent: Skip trash, delete permanently
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["delete"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if permanent:
        args.append("permanent")
    return run(args)


# ── Search ────────────────────────────────────────────────────────────────────

@mcp.tool()
def search(query: str, path: str = "", limit: int = 0, format: str = "", total: bool = False, case: bool = False, matches: bool = False, vault: str = "") -> str:
    """Search vault for text.

    Args:
        query: Search query (required)
        path: Limit to folder
        limit: Max results
        format: text|json
        total: Return match count only
        case: Case sensitive
        matches: Show match context
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["search", arg("query", query)]
    if path:
        args.append(arg("path", path))
    if limit:
        args.append(f"limit={limit}")
    if format:
        args.append(f"format={format}")
    if total:
        args.append("total")
    if case:
        args.append("case")
    if matches:
        args.append("matches")
    return run(args)


# ── Tags ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def tags_list(file: str = "", path: str = "", sort_by_count: bool = False, all: bool = False, total: bool = False, counts: bool = False, vault: str = "") -> str:
    """List tags.

    Args:
        file: File name (default: active file)
        path: File path
        sort_by_count: Sort by count
        all: List all tags in vault
        total: Return tag count only
        counts: Include tag counts
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["tags"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if sort_by_count:
        args.append("sort=count")
    if all:
        args.append("all")
    if total:
        args.append("total")
    if counts:
        args.append("counts")
    return run(args)


@mcp.tool()
def tag_info(name: str, total: bool = False, verbose: bool = False, vault: str = "") -> str:
    """Get tag info including files that use it.

    Args:
        name: Tag name (required)
        total: Return occurrence count only
        verbose: Include file list and count
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["tag", arg("name", name)]
    if total:
        args.append("total")
    if verbose:
        args.append("verbose")
    return run(args)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def tasks_list(file: str = "", path: str = "", status: str = "", all: bool = False, daily: bool = False, total: bool = False, done: bool = False, todo: bool = False, verbose: bool = False, vault: str = "") -> str:
    """List tasks.

    Args:
        file: Filter by file name
        path: Filter by file path
        status: Filter by status character
        all: List all tasks in vault
        daily: Show tasks from daily note
        total: Return task count only
        done: Show completed tasks
        todo: Show incomplete tasks
        verbose: Group by file with line numbers
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["tasks"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if status:
        args.append(arg("status", status))
    if all:
        args.append("all")
    if daily:
        args.append("daily")
    if total:
        args.append("total")
    if done:
        args.append("done")
    if todo:
        args.append("todo")
    if verbose:
        args.append("verbose")
    return run(args)


@mcp.tool()
def task_update(ref: str = "", file: str = "", path: str = "", line: int = 0, status: str = "", toggle: bool = False, daily: bool = False, done: bool = False, todo: bool = False, vault: str = "") -> str:
    """Show or update a task.

    Args:
        ref: Task reference as path:line
        file: File name
        path: File path
        line: Line number
        status: Set status character
        toggle: Toggle task status
        daily: Daily note
        done: Mark as done
        todo: Mark as todo
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["task"]
    if ref:
        args.append(arg("ref", ref))
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if line:
        args.append(f"line={line}")
    if status:
        args.append(arg("status", status))
    if toggle:
        args.append("toggle")
    if daily:
        args.append("daily")
    if done:
        args.append("done")
    if todo:
        args.append("todo")
    return run(args)


# ── Properties ────────────────────────────────────────────────────────────────

@mcp.tool()
def properties_list(file: str = "", path: str = "", name: str = "", sort_by_count: bool = False, format: str = "", all: bool = False, total: bool = False, counts: bool = False, vault: str = "") -> str:
    """List properties.

    Args:
        file: File name
        path: File path
        name: Get specific property
        sort_by_count: Sort by count
        format: yaml|tsv
        all: List all properties in vault
        total: Return property count only
        counts: Include occurrence counts
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["properties"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if name:
        args.append(arg("name", name))
    if sort_by_count:
        args.append("sort=count")
    if format:
        args.append(f"format={format}")
    if all:
        args.append("all")
    if total:
        args.append("total")
    if counts:
        args.append("counts")
    return run(args)


@mcp.tool()
def property_set(name: str, value: str, type: str = "", file: str = "", path: str = "", vault: str = "") -> str:
    """Set a property on a file.

    Args:
        name: Property name (required)
        value: Property value (required)
        type: text|list|number|checkbox|date|datetime
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["property:set", arg("name", name), arg("value", value)]
    if type:
        args.append(f"type={type}")
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def property_remove(name: str, file: str = "", path: str = "", vault: str = "") -> str:
    """Remove a property from a file.

    Args:
        name: Property name (required)
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["property:remove", arg("name", name)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def property_read(name: str, file: str = "", path: str = "", vault: str = "") -> str:
    """Read a property value from a file.

    Args:
        name: Property name (required)
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["property:read", arg("name", name)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


# ── Links ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def backlinks(file: str = "", path: str = "", counts: bool = False, total: bool = False, vault: str = "") -> str:
    """List backlinks to a file.

    Args:
        file: Target file name
        path: Target file path
        counts: Include link counts
        total: Return backlink count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["backlinks"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if counts:
        args.append("counts")
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def links(file: str = "", path: str = "", total: bool = False, vault: str = "") -> str:
    """List outgoing links from a file.

    Args:
        file: File name
        path: File path
        total: Return link count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["links"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def orphans(total: bool = False, all: bool = False, vault: str = "") -> str:
    """List files with no incoming links.

    Args:
        total: Return orphan count only
        all: Include non-markdown files
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["orphans"]
    if total:
        args.append("total")
    if all:
        args.append("all")
    return run(args)


@mcp.tool()
def unresolved_links(total: bool = False, counts: bool = False, vault: str = "") -> str:
    """List unresolved links in vault.

    Args:
        total: Return count only
        counts: Include link counts
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["unresolved"]
    if total:
        args.append("total")
    if counts:
        args.append("counts")
    return run(args)


# ── Templates ─────────────────────────────────────────────────────────────────

@mcp.tool()
def templates_list(total: bool = False, vault: str = "") -> str:
    """List templates.

    Args:
        total: Return template count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["templates"]
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def template_read(name: str, title: str = "", resolve: bool = False, vault: str = "") -> str:
    """Read template content.

    Args:
        name: Template name (required)
        title: Title for variable resolution
        resolve: Resolve template variables
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["template:read", arg("name", name)]
    if title:
        args.append(arg("title", title))
    if resolve:
        args.append("resolve")
    return run(args)


# ── Outline ───────────────────────────────────────────────────────────────────

@mcp.tool()
def outline(file: str = "", path: str = "", format: str = "", total: bool = False, vault: str = "") -> str:
    """Show headings for a file.

    Args:
        file: File name
        path: File path
        format: tree|md
        total: Return heading count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["outline"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if format:
        args.append(f"format={format}")
    if total:
        args.append("total")
    return run(args)


# ── Vault ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def vault_info(info: str = "", vault: str = "") -> str:
    """Show vault info.

    Args:
        info: name|path|files|folders|size — return specific info only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["vault"]
    if info:
        args.append(f"info={info}")
    return run(args)


@mcp.tool()
def vaults_list(total: bool = False, verbose: bool = False) -> str:
    """List all known vaults.

    Args:
        total: Return vault count only
        verbose: Include vault paths
    """
    args = ["vaults"]
    if total:
        args.append("total")
    if verbose:
        args.append("verbose")
    return run(args)


# ── File history ──────────────────────────────────────────────────────────────

@mcp.tool()
def diff(file: str = "", path: str = "", from_version: int = 0, to_version: int = 0, filter: str = "", vault: str = "") -> str:
    """List or compare versions from file history.

    Args:
        file: File name
        path: File path
        from_version: Version number to diff from
        to_version: Version number to diff to
        filter: local|sync
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["diff"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if from_version:
        args.append(f"from={from_version}")
    if to_version:
        args.append(f"to={to_version}")
    if filter:
        args.append(f"filter={filter}")
    return run(args)


@mcp.tool()
def history_read(file: str = "", path: str = "", version: int = 1, vault: str = "") -> str:
    """Read a local history version.

    Args:
        file: File name
        path: File path
        version: Version number (default: 1 = most recent)
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["history:read"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    args.append(f"version={version}")
    return run(args)


@mcp.tool()
def history_restore(version: int, file: str = "", path: str = "", vault: str = "") -> str:
    """Restore a local history version.

    Args:
        version: Version number (required)
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["history:restore", f"version={version}"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


# ── Bookmarks ─────────────────────────────────────────────────────────────────

@mcp.tool()
def bookmarks(total: bool = False, verbose: bool = False, vault: str = "") -> str:
    """List bookmarks.

    Args:
        total: Return bookmark count only
        verbose: Include bookmark types
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["bookmarks"]
    if total:
        args.append("total")
    if verbose:
        args.append("verbose")
    return run(args)


@mcp.tool()
def bookmark_add(file: str = "", folder: str = "", search: str = "", url: str = "", title: str = "", subpath: str = "", vault: str = "") -> str:
    """Add a bookmark.

    Args:
        file: File path to bookmark
        folder: Folder path to bookmark
        search: Search query to bookmark
        url: URL to bookmark
        title: Bookmark title
        subpath: Subpath (heading or block) within file
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["bookmark"]
    if file:
        args.append(arg("file", file))
    if folder:
        args.append(arg("folder", folder))
    if search:
        args.append(arg("search", search))
    if url:
        args.append(arg("url", url))
    if title:
        args.append(arg("title", title))
    if subpath:
        args.append(arg("subpath", subpath))
    return run(args)


# ── Random ────────────────────────────────────────────────────────────────────

@mcp.tool()
def random_note(folder: str = "", newtab: bool = False, silent: bool = False, vault: str = "") -> str:
    """Open a random note.

    Args:
        folder: Limit to folder
        newtab: Open in new tab
        silent: Return path without opening
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["random"]
    if folder:
        args.append(arg("folder", folder))
    if newtab:
        args.append("newtab")
    if silent:
        args.append("silent")
    return run(args)


@mcp.tool()
def random_read(folder: str = "", vault: str = "") -> str:
    """Read a random note (includes path).

    Args:
        folder: Limit to folder
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["random:read"]
    if folder:
        args.append(arg("folder", folder))
    return run(args)


# ── Word count ────────────────────────────────────────────────────────────────

@mcp.tool()
def wordcount(file: str = "", path: str = "", words: bool = False, characters: bool = False, vault: str = "") -> str:
    """Count words and characters in a file.

    Args:
        file: File name
        path: File path
        words: Return word count only
        characters: Return character count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["wordcount"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if words:
        args.append("words")
    if characters:
        args.append("characters")
    return run(args)


# ── Workspace ─────────────────────────────────────────────────────────────────

@mcp.tool()
def workspace_info(ids: bool = False, vault: str = "") -> str:
    """Show workspace tree.

    Args:
        ids: Include workspace item IDs
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["workspace"]
    if ids:
        args.append("ids")
    return run(args)


@mcp.tool()
def recents(total: bool = False, vault: str = "") -> str:
    """List recently opened files.

    Args:
        total: Return recent file count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["recents"]
    if total:
        args.append("total")
    return run(args)


# ── Aliases ───────────────────────────────────────────────────────────────────

@mcp.tool()
def aliases(file: str = "", path: str = "", all: bool = False, total: bool = False, verbose: bool = False, vault: str = "") -> str:
    """List aliases.

    Args:
        file: File name
        path: File path
        all: List all aliases in vault
        total: Return alias count only
        verbose: Include file paths
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["aliases"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if all:
        args.append("all")
    if total:
        args.append("total")
    if verbose:
        args.append("verbose")
    return run(args)


# ── Command palette ───────────────────────────────────────────────────────────

@mcp.tool()
def commands_list(filter: str = "", vault: str = "") -> str:
    """List available command IDs.

    Args:
        filter: Filter by ID prefix
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["commands"]
    if filter:
        args.append(arg("filter", filter))
    return run(args)


@mcp.tool()
def command_execute(id: str, vault: str = "") -> str:
    """Execute an Obsidian command by ID.

    Args:
        id: Command ID to execute (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["command", arg("id", id)])


# ── Sync ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def sync_status(vault: str = "") -> str:
    """Show sync status and usage.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["sync:status"])


# ── Sync (extended) ───────────────────────────────────────────────────────────

@mcp.tool()
def sync_toggle(on: bool = False, off: bool = False, vault: str = "") -> str:
    """Pause or resume Obsidian Sync.

    Args:
        on: Resume sync
        off: Pause sync
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["sync"]
    if on:
        args.append("on")
    if off:
        args.append("off")
    return run(args)


@mcp.tool()
def sync_deleted(total: bool = False, vault: str = "") -> str:
    """List deleted files in sync history.

    Args:
        total: Return deleted file count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["sync:deleted"]
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def sync_history(file: str = "", path: str = "", total: bool = False, vault: str = "") -> str:
    """List sync version history for a file.

    Args:
        file: File name
        path: File path
        total: Return version count only
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["sync:history"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if total:
        args.append("total")
    return run(args)


@mcp.tool()
def sync_read(version: int, file: str = "", path: str = "", vault: str = "") -> str:
    """Read a specific sync version of a file.

    Args:
        version: Version number (required)
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["sync:read", f"version={version}"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def sync_restore(version: int, file: str = "", path: str = "", vault: str = "") -> str:
    """Restore a specific sync version of a file.

    Args:
        version: Version number (required)
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["sync:restore", f"version={version}"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


# ── Plugins ───────────────────────────────────────────────────────────────────

@mcp.tool()
def plugins_list(filter: str = "", versions: bool = False, format: str = "", vault: str = "") -> str:
    """List all installed plugins (core and community).

    Args:
        filter: core|community — filter by plugin type
        versions: Include version numbers
        format: json|tsv|csv
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["plugins"]
    if filter:
        args.append(f"filter={filter}")
    if versions:
        args.append("versions")
    if format:
        args.append(f"format={format}")
    return run(args)


@mcp.tool()
def plugins_enabled(filter: str = "", versions: bool = False, format: str = "", vault: str = "") -> str:
    """List only enabled plugins.

    Args:
        filter: core|community — filter by plugin type
        versions: Include version numbers
        format: json|tsv|csv
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["plugins:enabled"]
    if filter:
        args.append(f"filter={filter}")
    if versions:
        args.append("versions")
    if format:
        args.append(f"format={format}")
    return run(args)


@mcp.tool()
def plugin_info(id: str, vault: str = "") -> str:
    """Get info about a specific plugin.

    Args:
        id: Plugin ID (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["plugin", arg("id", id)])


@mcp.tool()
def plugin_install(id: str, enable: bool = False, vault: str = "") -> str:
    """Install a community plugin by ID.

    Args:
        id: Plugin ID (required, e.g. 'view-count', 'dataview')
        enable: Enable the plugin after installing
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["plugin:install", arg("id", id)]
    if enable:
        args.append("enable")
    return run(args)


@mcp.tool()
def plugin_uninstall(id: str, vault: str = "") -> str:
    """Uninstall a community plugin.

    Args:
        id: Plugin ID (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["plugin:uninstall", arg("id", id)])


@mcp.tool()
def plugin_enable(id: str, vault: str = "") -> str:
    """Enable an installed plugin.

    Args:
        id: Plugin ID (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["plugin:enable", arg("id", id)])


@mcp.tool()
def plugin_disable(id: str, vault: str = "") -> str:
    """Disable a plugin.

    Args:
        id: Plugin ID (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["plugin:disable", arg("id", id)])


@mcp.tool()
def plugin_reload(id: str, vault: str = "") -> str:
    """Reload a plugin (useful for applying updates without restarting).

    Args:
        id: Plugin ID (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["plugin:reload", arg("id", id)])


@mcp.tool()
def plugins_restrict(on: bool = False, off: bool = False, vault: str = "") -> str:
    """Toggle restricted mode (disables all community plugins when on).

    Args:
        on: Enable restricted mode
        off: Disable restricted mode
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["plugins:restrict"]
    if on:
        args.append("on")
    if off:
        args.append("off")
    return run(args)


# ── Bases ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def bases_list(vault: str = "") -> str:
    """List all base files in the vault (Obsidian Bases feature).

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["bases"])


@mcp.tool()
def base_views(file: str = "", path: str = "", vault: str = "") -> str:
    """List views in a base file.

    Args:
        file: Base file name
        path: Base file path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["base:views"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def base_query(file: str = "", path: str = "", view: str = "", format: str = "", vault: str = "") -> str:
    """Query a base and return results.

    Args:
        file: Base file name
        path: Base file path
        view: View name to query
        format: json|csv|tsv|md|paths
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["base:query"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if view:
        args.append(arg("view", view))
    if format:
        args.append(f"format={format}")
    return run(args)


@mcp.tool()
def base_create(name: str, file: str = "", path: str = "", view: str = "", content: str = "", vault: str = "") -> str:
    """Create a new item in a base.

    Args:
        name: New file name (required)
        file: Base file name
        path: Base file path
        view: View name
        content: Initial content
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["base:create", arg("name", name)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    if view:
        args.append(arg("view", view))
    if content:
        args.append(arg("content", content))
    return run(args)


# ── Themes ────────────────────────────────────────────────────────────────────

@mcp.tool()
def themes_list(versions: bool = False, vault: str = "") -> str:
    """List installed themes.

    Args:
        versions: Include version numbers
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["themes"]
    if versions:
        args.append("versions")
    return run(args)


@mcp.tool()
def theme_info(name: str = "", vault: str = "") -> str:
    """Show active theme or get info about a specific theme.

    Args:
        name: Theme name (omit to show currently active theme)
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["theme"]
    if name:
        args.append(arg("name", name))
    return run(args)


@mcp.tool()
def theme_set(name: str, vault: str = "") -> str:
    """Set the active theme.

    Args:
        name: Theme name (required, pass empty string for default theme)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["theme:set", arg("name", name)])


@mcp.tool()
def theme_install(name: str, enable: bool = False, vault: str = "") -> str:
    """Install a community theme.

    Args:
        name: Theme name (required)
        enable: Activate after installing
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["theme:install", arg("name", name)]
    if enable:
        args.append("enable")
    return run(args)


@mcp.tool()
def theme_uninstall(name: str, vault: str = "") -> str:
    """Uninstall a theme.

    Args:
        name: Theme name (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["theme:uninstall", arg("name", name)])


# ── CSS Snippets ──────────────────────────────────────────────────────────────

@mcp.tool()
def snippets_list(vault: str = "") -> str:
    """List all installed CSS snippets.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["snippets"])


@mcp.tool()
def snippets_enabled(vault: str = "") -> str:
    """List currently enabled CSS snippets.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["snippets:enabled"])


@mcp.tool()
def snippet_enable(name: str, vault: str = "") -> str:
    """Enable a CSS snippet.

    Args:
        name: Snippet name (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["snippet:enable", arg("name", name)])


@mcp.tool()
def snippet_disable(name: str, vault: str = "") -> str:
    """Disable a CSS snippet.

    Args:
        name: Snippet name (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["snippet:disable", arg("name", name)])


# ── Tabs ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def tabs_list(ids: bool = False, vault: str = "") -> str:
    """List currently open tabs.

    Args:
        ids: Include tab IDs
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["tabs"]
    if ids:
        args.append("ids")
    return run(args)


@mcp.tool()
def tab_open(file: str = "", group: str = "", view: str = "", vault: str = "") -> str:
    """Open a new tab, optionally with a file or view.

    Args:
        file: File to open in the new tab
        group: Tab group ID
        view: View type to open
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["tab:open"]
    if file:
        args.append(arg("file", file))
    if group:
        args.append(arg("group", group))
    if view:
        args.append(arg("view", view))
    return run(args)


# ── Hotkeys ───────────────────────────────────────────────────────────────────

@mcp.tool()
def hotkeys_list(total: bool = False, verbose: bool = False, all: bool = False, format: str = "", vault: str = "") -> str:
    """List hotkeys.

    Args:
        total: Return hotkey count only
        verbose: Show if each hotkey is custom or default
        all: Include commands without hotkeys
        format: json|tsv|csv
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["hotkeys"]
    if total:
        args.append("total")
    if verbose:
        args.append("verbose")
    if all:
        args.append("all")
    if format:
        args.append(f"format={format}")
    return run(args)


@mcp.tool()
def hotkey_info(id: str, verbose: bool = False, vault: str = "") -> str:
    """Get the hotkey assigned to a specific command.

    Args:
        id: Command ID (required)
        verbose: Show if custom or default
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["hotkey", arg("id", id)]
    if verbose:
        args.append("verbose")
    return run(args)


# ── Files (extended) ──────────────────────────────────────────────────────────

@mcp.tool()
def file_rename(name: str, file: str = "", path: str = "", vault: str = "") -> str:
    """Rename a file in place (stays in same folder, unlike file_move).

    Args:
        name: New file name (required)
        file: Current file name
        path: Current file path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["rename", arg("name", name)]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def deadends(total: bool = False, all: bool = False, vault: str = "") -> str:
    """List files with no outgoing links (graph dead ends).

    Args:
        total: Return dead-end count only
        all: Include non-markdown files
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["deadends"]
    if total:
        args.append("total")
    if all:
        args.append("all")
    return run(args)


# ── Search (extended) ─────────────────────────────────────────────────────────

@mcp.tool()
def search_context(query: str, path: str = "", limit: int = 0, case: bool = False, format: str = "", vault: str = "") -> str:
    """Search vault and return matching lines with surrounding context.
    More useful than search() when you need to see what matched, not just which files.

    Args:
        query: Search query (required)
        path: Limit search to folder
        limit: Max results
        case: Case sensitive
        format: text|json
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["search:context", arg("query", query)]
    if path:
        args.append(arg("path", path))
    if limit:
        args.append(f"limit={limit}")
    if case:
        args.append("case")
    if format:
        args.append(f"format={format}")
    return run(args)


# ── History (extended) ────────────────────────────────────────────────────────

@mcp.tool()
def history_versions(file: str = "", path: str = "", vault: str = "") -> str:
    """List available local history versions for a file.

    Args:
        file: File name
        path: File path
        vault: Target vault name (optional)
    """
    args = vault_prefix(vault) + ["history"]
    if file:
        args.append(arg("file", file))
    if path:
        args.append(arg("path", path))
    return run(args)


@mcp.tool()
def history_list(vault: str = "") -> str:
    """List all files that have local history entries.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["history:list"])


# ── Daily (extended) ──────────────────────────────────────────────────────────

@mcp.tool()
def daily_path(vault: str = "") -> str:
    """Get the file path of today's daily note without opening it.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["daily:path"])


# ── Templates (extended) ──────────────────────────────────────────────────────

@mcp.tool()
def template_insert(name: str, vault: str = "") -> str:
    """Insert a template into the currently active file in Obsidian.

    Args:
        name: Template name (required)
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["template:insert", arg("name", name)])


# ── Vault (extended) ──────────────────────────────────────────────────────────

@mcp.tool()
def vault_reload(vault: str = "") -> str:
    """Reload the vault (refreshes file index without restarting).

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["reload"])


@mcp.tool()
def app_restart(vault: str = "") -> str:
    """Restart the Obsidian app.

    Args:
        vault: Target vault name (optional)
    """
    return run(vault_prefix(vault) + ["restart"])


# ── Binary Attachments ────────────────────────────────────────────────────────
#
# The Obsidian CLI only handles text. These two tools bypass it entirely and
# read/write binary files directly on disk using the vault path returned by
# `vault_info(info="path")`.
#
# The MCP server runs on the same machine as Obsidian, so it has direct
# filesystem access — no subprocess, no base64 corruption.
#
# Supported types (non-exhaustive):
#   Documents : pdf, docx, xlsx, pptx, odt, ods, odp, rtf, epub
#   Images    : png, jpg, jpeg, gif, webp, svg, bmp, tiff, ico, heic, avif
#   Audio     : mp3, wav, aac, flac, ogg, m4a, opus
#   Video     : mp4, mov, avi, mkv, webm, m4v
#   Archives  : zip, tar, gz, bz2, 7z, rar
#   Data      : csv, json, xml, parquet, db, sqlite
#   Other     : any binary — the tool is format-agnostic

import base64
import json as _json
from pathlib import Path


def _vault_root(vault: str = "") -> Path:
    """Return the absolute filesystem path to a vault root via the CLI."""
    raw = vault_info(info="path", vault=vault)
    return Path(raw.strip())


# @mcp.tool()
# def write_attachment(
#     dest_path: str,
#     content_b64: str,
#     vault: str = "",
#     overwrite: bool = False,
# ) -> str:
#     """Write a binary attachment (PDF, image, Office doc, audio, video, archive, …)
#     directly to the vault filesystem.  Use this for any file that is not plain
#     text — the Obsidian CLI cannot handle binary content.

#     Because the MCP server runs on the same machine as Obsidian, this writes
#     directly to the vault folder on disk.  Call vault_reload() afterwards so
#     Obsidian picks up the new file immediately.

#     Args:
#         dest_path : Path relative to the vault root, e.g. "artifacts/report.pdf"
#                     or "attachments/diagram.png".  Parent directories are created
#                     automatically.
#         content_b64 : Standard Base64-encoded bytes of the file to write.
#         vault     : Target vault name (optional, defaults to active vault).
#         overwrite : If False (default) raises FileExistsError when the file
#                     already exists, preventing accidental overwrites.  Pass
#                     True to replace an existing file.

#     Returns:
#         Human-readable confirmation with the absolute path and byte count.

#     Supported attachment types (non-exhaustive):
#         pdf  docx  xlsx  pptx  odt  ods  odp  rtf  epub
#         png  jpg  jpeg  gif  webp  svg  bmp  tiff  heic  avif  ico
#         mp3  wav  aac  flac  ogg  m4a  opus
#         mp4  mov  avi  mkv  webm  m4v
#         zip  tar  gz  bz2  7z  rar
#         csv  json  xml  parquet  db  sqlite
#         … and any other binary format
#     """
#     root = _vault_root(vault)
#     dest = root / dest_path

#     if dest.exists() and not overwrite:
#         raise FileExistsError(
#             f"File already exists: {dest}  —  pass overwrite=True to replace it."
#         )

#     dest.parent.mkdir(parents=True, exist_ok=True)

#     data = base64.b64decode(content_b64)
#     dest.write_bytes(data)

#     return f"OK  {len(data):,} bytes  →  {dest}"


# @mcp.tool()
# def read_attachment_base64(
#     src_path: str,
#     vault: str = "",
# ) -> str:
#     """Read a binary attachment from the vault and return it as Base64.

#     Use this to retrieve any non-text file stored in the vault — PDFs,
#     images, Office documents, audio, video — so that Claude or another tool
#     can inspect, transform, or forward it.

#     Args:
#         src_path : Path relative to the vault root, e.g. "artifacts/report.pdf".
#         vault    : Target vault name (optional, defaults to active vault).

#     Returns:
#         JSON object:
#           {
#             "path"    : "<absolute path read>",
#             "size"    : <bytes as int>,
#             "content" : "<standard Base64 string>"
#           }
#     """
#     root = _vault_root(vault)
#     src = root / src_path

#     if not src.exists():
#         raise FileNotFoundError(f"File not found in vault: {src}")

#     data = src.read_bytes()
#     return _json.dumps({
#         "path":    str(src),
#         "size":    len(data),
#         "content": base64.b64encode(data).decode("ascii"),
#     })


if __name__ == "__main__":
    mcp.run(transport="stdio")