#!/usr/bin/env python3
"""
install.py — Cross-platform installer for Sigil
Works on macOS, Linux, and Windows.

The venv is stored in a local cache directory (NOT inside the repo)
so it never gets synced via Google Drive / iCloud / OneDrive.

Usage:
    python install.py
    python install.py --dry-run
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def header(text: str):
    print(f"\n{'─' * 50}")
    print(f"  {text}")
    print(f"{'─' * 50}")

def ok(text: str):
    print(f"  ✅ {text}")

def warn(text: str):
    print(f"  ⚠️  {text}")

def info(text: str):
    print(f"  ℹ️  {text}")

def fail(text: str):
    print(f"  ❌ {text}")
    sys.exit(1)


# ── Platform detection ────────────────────────────────────────────────────────

def get_platform() -> str:
    system = platform.system()
    if system == "Darwin":
        return "mac"
    elif system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    else:
        fail(f"Unsupported platform: {system}")


def get_claude_config_path() -> Path:
    p = get_platform()
    if p == "mac":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif p == "windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    else:  # linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def get_local_venv_dir(script_dir: Path) -> Path:
    """
    Return a local (non-synced) directory to store the venv.

    Uses the platform cache dir so the venv never ends up inside
    Google Drive / iCloud / OneDrive.

    Mac:     ~/Library/Caches/sigil
    Windows: %LOCALAPPDATA%/sigil
    Linux:   ~/.cache/sigil
    """
    p = get_platform()
    # Use a hash of the script_dir so multiple installs don't collide
    import hashlib
    dir_hash = hashlib.md5(str(script_dir).encode()).hexdigest()[:8]
    name = f"sigil-{dir_hash}"

    if p == "mac":
        return Path.home() / "Library" / "Caches" / name
    elif p == "windows":
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local_app_data) / name
    else:  # linux
        xdg_cache = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        return Path(xdg_cache) / name


# ── uv ────────────────────────────────────────────────────────────────────────

def ensure_uv() -> Path:
    header("Checking uv")
    uv = shutil.which("uv")
    if uv:
        ok(f"uv found: {uv}")
        return Path(uv)

    warn("uv not found — installing...")
    p = get_platform()
    try:
        if p == "windows":
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "ByPass", "-c",
                 "irm https://astral.sh/uv/install.ps1 | iex"],
                check=True
            )
            user_path = subprocess.check_output(
                ["powershell", "-c", "[System.Environment]::GetEnvironmentVariable('PATH','User')"],
                text=True
            ).strip()
            os.environ["PATH"] = user_path + ";" + os.environ.get("PATH", "")
        else:
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True, check=True
            )
            local_bin = Path.home() / ".local" / "bin"
            os.environ["PATH"] = str(local_bin) + ":" + os.environ.get("PATH", "")
    except subprocess.CalledProcessError:
        fail("Failed to install uv. Install manually: https://docs.astral.sh/uv/getting-started/installation/")

    uv = shutil.which("uv")
    if not uv:
        fail("uv installed but not found in PATH. Restart your terminal and re-run.")
    ok(f"uv installed: {uv}")
    return Path(uv)


# ── Dependencies ──────────────────────────────────────────────────────────────

def install_dependencies(script_dir: Path, venv_dir: Path, dry_run: bool):
    header("Installing Python dependencies")
    info(f"Venv location: {venv_dir}")

    if dry_run:
        info(f"DRY RUN: would run `uv sync` with venv at {venv_dir}")
        return

    venv_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "sync", "--project", str(script_dir)],
        env={**os.environ, "UV_PROJECT_ENVIRONMENT": str(venv_dir)},
        check=True
    )
    ok("Dependencies installed")


# ── Obsidian CLI check ────────────────────────────────────────────────────────

def check_obsidian_cli():
    header("Checking Obsidian CLI")
    p = get_platform()

    if shutil.which("obsidian"):
        ok("obsidian CLI found in PATH")
        return

    if p == "mac":
        default = Path("/Applications/Obsidian.app/Contents/MacOS/Obsidian")
        if default.exists():
            ok(f"obsidian CLI found at: {default}")
            warn("Not in PATH — add this to ~/.zprofile or ~/.zshrc:")
            info('  export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"')
            return

    warn("obsidian CLI not found.")
    info("To enable it: Obsidian → Settings → General → Enable Command line interface")
    if p == "windows":
        info("Also needed: Obsidian.com file from #insider-desktop-release on Discord")
    elif p == "mac":
        info("Then add to ~/.zprofile:")
        info('  export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"')


# ── Claude Desktop config ─────────────────────────────────────────────────────

def configure_claude(script_dir: Path, venv_dir: Path, uv_path: Path, dry_run: bool):
    header("Configuring Claude Desktop")

    config_file = get_claude_config_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    new_entry = {
        "command": str(uv_path),
        "args": [
            "--directory", str(script_dir),
            "run",
            "server.py"
        ],
        "env": {
            "UV_PROJECT_ENVIRONMENT": str(venv_dir)
        }
    }

    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {}

    config.setdefault("mcpServers", {})
    existing = config["mcpServers"].get("sigil")

    if existing == new_entry:
        ok("Claude config already up to date")
        return

    config["mcpServers"]["sigil"] = new_entry

    if dry_run:
        info(f"DRY RUN: would write to {config_file}:")
        print(json.dumps({"mcpServers": {"sigil": new_entry}}, indent=2))
        return

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    ok(f"Config written: {config_file}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Install Sigil and configure Claude Desktop"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    args = parser.parse_args()

    print("\n🔧 Sigil installer")
    print(f"   Platform: {platform.system()} {platform.machine()}")
    if args.dry_run:
        print("   Mode: DRY RUN (no changes will be made)")

    script_dir = Path(__file__).parent.resolve()
    venv_dir = get_local_venv_dir(script_dir)

    uv_path = ensure_uv()
    install_dependencies(script_dir, venv_dir, args.dry_run)
    check_obsidian_cli()
    configure_claude(script_dir, venv_dir, uv_path, args.dry_run)

    header("Done")
    ok("Restart Claude Desktop to connect.")
    if not args.dry_run:
        print()
        info("Test it by asking Claude: 'what vaults can you see?'")
        info(f"Venv stored at: {venv_dir}")
    print()


if __name__ == "__main__":
    main()