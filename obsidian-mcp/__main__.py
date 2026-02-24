"""
Sigil for Obsidian – entry point for both pip-installed and .mcpb usage.

When launched from a .mcpb extension, dependencies may not be installed yet.
This module:
  1. Adds the parent directory to sys.path (so package imports work)
  2. Auto-installs missing deps on first run (with lock-file to prevent races)
  3. Imports and starts the MCP server
"""

import os
import sys
import time
import subprocess
import importlib
import tempfile

# ── 1. Fix sys.path so `from mcp.server.fastmcp import FastMCP` resolves
#        even when not pip-installed (i.e. running from extracted .mcpb)
_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)
if _parent not in sys.path:
    sys.path.insert(0, _parent)


# ── 2. Auto-install missing dependencies
DEPS = {
    "mcp": "mcp[cli]>=1.2.0",
}

_lock_path = os.path.join(tempfile.gettempdir(), "sigil-install.lock")


def _ensure_deps():
    """Install any missing dependencies, once."""
    missing = []
    for mod_name, pip_spec in DEPS.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing.append(pip_spec)

    if not missing:
        return

    # Lock-file: if another instance is already installing, wait for it
    if os.path.exists(_lock_path):
        print("[sigil] Another instance is installing deps, waiting…", file=sys.stderr)
        deadline = time.time() + 60
        while os.path.exists(_lock_path) and time.time() < deadline:
            time.sleep(2)
        # Re-check after waiting
        still_missing = []
        for mod_name, pip_spec in DEPS.items():
            try:
                importlib.import_module(mod_name)
            except ImportError:
                still_missing.append(pip_spec)
        if not still_missing:
            return
        missing = still_missing

    # Write lock
    try:
        with open(_lock_path, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass

    try:
        print(f"[sigil] Installing: {', '.join(missing)}", file=sys.stderr)
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        try:
            subprocess.check_call(cmd, timeout=120)
        except (subprocess.CalledProcessError, PermissionError):
            # Retry with --user flag
            cmd_user = [sys.executable, "-m", "pip", "install", "--user"] + missing
            try:
                subprocess.check_call(cmd_user, timeout=120)
            except Exception as e:
                print(
                    f"[sigil] Auto-install failed: {e}\n"
                    f"  Please run manually:  {sys.executable} -m pip install {' '.join(missing)}",
                    file=sys.stderr,
                )
                sys.exit(1)
    finally:
        # Remove lock
        try:
            os.remove(_lock_path)
        except OSError:
            pass


# ── 3. Run the server
def main():
    _ensure_deps()

    # Import after deps are available
    from server import mcp  # noqa: E402
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
