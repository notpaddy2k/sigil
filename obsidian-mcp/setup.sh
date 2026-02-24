#!/bin/bash
# setup.sh — Install Sigil and configure Claude Desktop
# macOS and Linux

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 Checking for uv..."
if ! command -v uv &>/dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "✅ uv: $(uv --version)"

echo ""
echo "📦 Installing dependencies..."
cd "$SCRIPT_DIR"
uv sync
echo "✅ Done"

echo ""
echo "🔍 Checking Obsidian CLI..."
if command -v obsidian &>/dev/null; then
    echo "✅ obsidian CLI found"
else
    echo "⚠️  obsidian not in PATH."
    echo "   Settings → General → Enable Command line interface"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo ""
        echo "   Add to ~/.zprofile:"
        echo '   export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"'
    fi
fi

echo ""
echo "📝 Configuring Claude Desktop..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
else
    CONFIG_DIR="$HOME/.config/Claude"
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
mkdir -p "$CONFIG_DIR"
UV_PATH=$(command -v uv)

python3 - <<PYEOF
import json, os

config_file = "$CONFIG_FILE"
script_dir = "$SCRIPT_DIR"
uv_path = "$UV_PATH"

new_entry = {
    "command": uv_path,
    "args": ["--directory", script_dir, "run", "server.py"]
}

if os.path.exists(config_file):
    with open(config_file) as f:
        config = json.load(f)
else:
    config = {}

config.setdefault("mcpServers", {})
config["mcpServers"]["sigil"] = new_entry

with open(config_file, "w") as f:
    json.dump(config, f, indent=2)

print(f"✅ Config written to: {config_file}")
PYEOF

echo ""
echo "✅ Done! Restart Claude Desktop to connect."
echo ""
echo "📁 Copy the skills to your vault:"
echo "   cp $SCRIPT_DIR/skills/obsidian.md ~/path/to/vault/.claude/skills/obsidian.md"
echo "   cp $SCRIPT_DIR/skills/obsidian-review.md ~/path/to/vault/.claude/skills/obsidian-review.md"
