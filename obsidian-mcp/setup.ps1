# setup.ps1 — Install Sigil and configure Claude Desktop
# Run: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "🔍 Checking for uv..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH
}
Write-Host "✅ uv: $(uv --version)" -ForegroundColor Green

Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
Set-Location $ScriptDir
uv sync
Write-Host "✅ Done" -ForegroundColor Green

Write-Host ""
Write-Host "🔍 Checking Obsidian CLI..." -ForegroundColor Cyan
if (Get-Command obsidian -ErrorAction SilentlyContinue) {
    Write-Host "✅ obsidian CLI found" -ForegroundColor Green
} else {
    Write-Host "⚠️  obsidian not in PATH." -ForegroundColor Yellow
    Write-Host "   Settings → General → Enable Command line interface"
    Write-Host "   Also need Obsidian.com file from #insider-desktop-release on Discord"
}

Write-Host ""
Write-Host "📝 Configuring Claude Desktop..." -ForegroundColor Cyan

$ConfigDir = Join-Path $env:APPDATA "Claude"
$ConfigFile = Join-Path $ConfigDir "claude_desktop_config.json"
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

$UvPath = (Get-Command uv).Source

$NewEntry = @{
    command = $UvPath
    args = @("--directory", $ScriptDir, "run", "server.py")
}

if (Test-Path $ConfigFile) {
    $Config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
} else {
    $Config = @{}
}

if (-not $Config.mcpServers) {
    $Config | Add-Member -NotePropertyName mcpServers -NotePropertyValue @{}
}
$Config.mcpServers | Add-Member -NotePropertyName sigil -NotePropertyValue $NewEntry -Force
$Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile

Write-Host "✅ Config: $ConfigFile" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Done! Restart Claude Desktop to connect." -ForegroundColor Green
Write-Host ""
Write-Host "📁 Copy skills to your vault:" -ForegroundColor Cyan
Write-Host "   $ScriptDir\skills\obsidian.md → your-vault\.claude\skills\obsidian.md"
Write-Host "   $ScriptDir\skills\obsidian-review.md → your-vault\.claude\skills\obsidian-review.md"
