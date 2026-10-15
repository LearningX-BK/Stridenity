<#
.SYNOPSIS
  Binds C:\GenAIGenerated\Stridenity\Compliance to the Compliance/ folder of
  https://github.com/LearningX-BK/Stridenity.git (ADR-013) — run once per machine.

.DESCRIPTION
  The GitHub repo is Stridenity's product monorepo; this product is its Compliance/ folder. Git
  needs the repo root to be the PARENT folder (C:\GenAIGenerated\Stridenity). To avoid touching
  sibling folders there (e.g. HMS), this script uses a sparse checkout (only Compliance/ + root
  files like CLAUDE.md, .claude/, .github/) and a local exclude list so other folders are invisible
  to git.

  After it runs:
    cd C:\GenAIGenerated\Stridenity\Compliance
    git pull          # get cloud-session work
    git push          # publish local work
  Both the build loop and cloud sessions commit and push for you.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\GenAIGenerated\Stridenity\Compliance\scripts\setup-git-sync.ps1
  ... -Force        # do not ask before making the folder match GitHub exactly
#>
[CmdletBinding()]
param(
  [string]$RepoUrl = "https://github.com/LearningX-BK/Stridenity.git",
  [string]$Branch = "main",
  [switch]$Force
)
$ErrorActionPreference = "Stop"
$compliance = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $compliance
if ((Split-Path -Leaf $compliance) -ne "Compliance") { throw "Expected to live in <root>\Compliance\scripts (found $compliance)" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git not found. Install: winget install Git.Git" }
Write-Host "Repo root (parent): $root" -ForegroundColor Cyan
Set-Location $root

$prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
if (Test-Path (Join-Path $root ".git")) {
  $origin = (git remote get-url origin 2>$null | Out-String).Trim()
  if ($origin -and ($origin.TrimEnd('/') -replace '\.git$','') -ne ($RepoUrl -replace '\.git$','')) {
    $ErrorActionPreference = $prevEap
    throw "$root is already a git repo with origin '$origin'. Not touching it - resolve manually."
  }
  if (-not $origin) { git remote add origin $RepoUrl }
  Write-Host "Existing repo found - refreshing sparse checkout." -ForegroundColor Yellow
} else {
  git init -b $Branch | Out-Host
  git remote add origin $RepoUrl
}
git config core.autocrlf false        # .gitattributes controls line endings
git config pull.rebase true
git config rebase.autoStash true
git fetch origin $Branch | Out-Host
if ($LASTEXITCODE -ne 0) { $ErrorActionPreference = $prevEap; throw "fetch failed - check GitHub login (git credential manager will prompt)." }

git sparse-checkout init --cone | Out-Null
git sparse-checkout set Compliance | Out-Null

# Hide sibling product folders from git status (local only, never committed)
$exclude = Join-Path $root ".git\info\exclude"
$lines = @("# setup-git-sync.ps1: only Compliance/ and root config are part of this checkout",
           "/*", "!/Compliance/", "!/.claude/", "!/.github/", "!/CLAUDE.md", "!/README.md",
           "!/.gitignore", "!/.gitattributes")
Set-Content -Path $exclude -Value $lines -Encoding ascii

$current = (git rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
if ($current -ne $Branch) { git checkout -B $Branch 2>$null | Out-Null }
git reset --mixed "origin/$Branch" | Out-Null       # index = GitHub, files untouched
git branch --set-upstream-to="origin/$Branch" $Branch | Out-Null

$changes = git status --short -- Compliance CLAUDE.md .claude .github README.md .gitignore .gitattributes
if ($changes) {
  Write-Host "`nDifferences between this folder and GitHub:" -ForegroundColor Yellow
  $changes | Select-Object -First 30 | Out-Host
  $ans = if ($Force) { "y" } else { Read-Host "Make the folder match GitHub exactly (local-only changes listed above are overwritten)? [y/N]" }
  if ($ans -match '^(y|yes)$') {
    git checkout -- . | Out-Null
    Write-Host "Folder now matches origin/$Branch." -ForegroundColor Green
  } else {
    Write-Host "Left as is. Review with: git -C `"$root`" status" -ForegroundColor Yellow
  }
} else {
  Write-Host "Folder already matches origin/$Branch." -ForegroundColor Green
}
$ErrorActionPreference = $prevEap
git log --oneline -3 | Out-Host
Write-Host "`nDone. Work from: $compliance  (git pull / push work from there)." -ForegroundColor Cyan
