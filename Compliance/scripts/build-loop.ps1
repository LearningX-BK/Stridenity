<#
.SYNOPSIS
  Drives the ANUPAL (Stridenity Compliance) build task-by-task with Claude Code in headless mode, surviving usage-limit
  windows. Each iteration = one fresh Claude session running /next-task (one task, checkpointed).

.EXAMPLES
  Run from the Compliance folder (C:\GenAIGenerated\Stridenity\Compliance). The git repo root is the
  parent folder (sparse checkout, see scripts/setup-git-sync.ps1); git commands work from here.

  .\scripts\build-loop.ps1                       # per-task recommended model (opus/sonnet), run until done
  .\scripts\build-loop.ps1 -Once                 # just the next task (may take several short sessions)
  .\scripts\build-loop.ps1 -Steps 3              # bigger sessions (default 2 sub-steps per session)
  .\scripts\build-loop.ps1 -PauseAfter task      # ask "continue?" after every finished task
  .\scripts\build-loop.ps1 -PauseAfter session   # ask after every Claude session (each 2-step chunk)
  New-Item PAUSE                                 # (2nd window) stop a running loop cleanly after its current session
  .\scripts\build-loop.ps1 -Model sonnet         # force a model for every task (save Opus budget)
  .\scripts\build-loop.ps1 -Model claude-opus-5-5 -StopAt T08
  .\scripts\build-loop.ps1 -WaitOnLimit:$false   # stop instead of sleeping when the limit is hit
  .\scripts\build-loop.ps1 -SkipPermissions      # fully unattended (bypasses permission checks - your call)

.NOTES
  Works on Windows PowerShell 5.1 and PowerShell 7. Requires: git, claude, and a working Python (uv, py launcher, or python) on PATH.
  Logs: .build-logs\<timestamp>-<task>.log (git-ignored).
#>
[CmdletBinding()]
param(
  [string]$Model = "auto",            # auto = use the task's recommended model
  [string]$FallbackModel = "sonnet",
  [switch]$Once,
  [string]$StopAt = "",               # stop after this task id completes
  [bool]$WaitOnLimit = $true,
  [int]$DefaultWaitMinutes = 30,
  [int]$MaxNoProgress = 2,
  [switch]$SkipPermissions,
  [string]$Steps = "2",               # sub-steps per Claude session (small sessions = small context = cheaper). "all" = no cap
  [string]$Prompt = "",               # default: "/next-task steps=$Steps"
  [ValidateSet("none", "task", "session")]
  [string]$PauseAfter = "none",       # ask before continuing: after each finished task, or after every session
  [switch]$ForceLock                  # take the builder lock even if a cloud session holds it (ADR-014)
)
if (-not $Prompt) { $Prompt = "/next-task steps=$Steps" }

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$logDir = Join-Path $root ".build-logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$env:PYTHONUTF8 = "1"

# Find a Python that actually runs. Bare `python` on Windows can be the Microsoft Store alias
# ("Python was not found...") and can change mid-run, so test-run each candidate and re-check every iteration.
function Resolve-Py {
  $cands = @(
    @{ exe = "uv";      pre = @("run", "--no-project", "--quiet", "python") },
    @{ exe = "py";      pre = @("-3") },
    @{ exe = "python";  pre = @() },
    @{ exe = "python3"; pre = @() }
  )
  foreach ($c in $cands) {
    if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
    $out = & $c.exe @($c.pre + @("-c", "print(42)")) 2>$null
    if ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq "42") { return $c }
  }
  throw "No working Python found (tried uv, py, python, python3). Install uv: winget install astral-sh.uv"
}
function Invoke-Py([string[]]$PyArgs) {
  $script:py = Resolve-Py
  & $script:py.exe @($script:py.pre + $PyArgs)
}

function Get-NextTask {
  $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
  $json = Invoke-Py @("scripts/tasks.py", "next", "--json") 2>$null | Out-String
  try { $state = $json | ConvertFrom-Json }
  catch {
    $err = Invoke-Py @("scripts/tasks.py", "next", "--json") 2>&1 | Out-String
    $ErrorActionPreference = $prev
    throw "scripts/tasks.py did not return JSON (Python problem?). Output:`n$err"
  }
  $ErrorActionPreference = $prev
  return $state
}
function Get-DoneCount {
  $d = Get-Content docs/plan/tasks.json -Raw -Encoding UTF8 | ConvertFrom-Json
  return @($d.tasks | Where-Object { $_.status -eq "done" }).Count
}
function Get-Head { (& git rev-parse HEAD 2>$null | Out-String).Trim() }

function Get-LimitWaitSeconds([string]$text) {
  # Returns seconds to wait if output looks like a usage/rate limit, else -1.
  # e.g. "You've hit your session limit - resets 6:30pm (Asia/Kolkata)"
  if ($text -notmatch '(?i)(session limit|weekly limit|usage limit|hit your|limit reached|rate limit|limit will reset|resets at|5-hour|overloaded|429)') { return -1 }
  if ($text -match '\|(\d{10})') {
    $reset = [DateTimeOffset]::FromUnixTimeSeconds([int64]$Matches[1]).LocalDateTime
    $secs = [int]([Math]::Ceiling(($reset - (Get-Date)).TotalSeconds)) + 120
    if ($secs -gt 0) { return $secs }
  }
  if ($text -match '(?i)resets? (?:at )?(\d{1,2})(?::(\d{2}))?\s*(am|pm)') {
    $h = [int]$Matches[1]; $m = 0; if ($Matches[2]) { $m = [int]$Matches[2] }
    if ($Matches[3] -ieq 'pm' -and $h -lt 12) { $h += 12 }; if ($Matches[3] -ieq 'am' -and $h -eq 12) { $h = 0 }
    $t = (Get-Date).Date.AddHours($h).AddMinutes($m); if ($t -lt (Get-Date)) { $t = $t.AddDays(1) }
    return [int]([Math]::Ceiling(($t - (Get-Date)).TotalSeconds)) + 120
  }
  return $DefaultWaitMinutes * 60
}

# A file named PAUSE in the repo root stops the loop cleanly before the next session starts
# (create it from another window: `New-Item PAUSE`). It is removed when honoured. Git-ignored.
$pauseFile = Join-Path $root "PAUSE"

# Returns $true to continue. [A]lways stops asking for the rest of this run.
function Request-Continue([string]$what) {
  Invoke-Py @("scripts/tasks.py", "next") | Out-Host
  $ans = Read-Host "$what - continue? [Y]es / [N]o, stop here / [A]lways (stop asking)"
  if ($ans -match '^(n|no)$') { Write-Host "Paused. Re-run the same command to resume; progress is committed." -ForegroundColor Yellow; return $false }
  if ($ans -match '^(a|always)$') { $script:PauseAfter = "none" }
  return $true
}

$noProgress = 0
Write-Host "ANUPAL build loop - folder: $root  (pause: -PauseAfter task|session, or create a PAUSE file)" -ForegroundColor Cyan

while ($true) {
  if (Test-Path $pauseFile) {
    Remove-Item $pauseFile -Force
    Write-Host "PAUSE file found - stopping here. Progress is committed; re-run to resume." -ForegroundColor Yellow
    break
  }
  git pull --rebase --autostash | Out-Host
  $state = Get-NextTask
  if (-not $state.task) {
    if ($state.remaining -eq 0) { Write-Host "All tasks done." -ForegroundColor Green }
    else { Write-Host "No runnable task. Blocked: $($state.blocked -join ', '). Resolve and re-run." -ForegroundColor Yellow }
    break
  }
  $task = $state.task
  # One builder at a time (ADR-014): claim/refresh the lock, commit + push it so cloud sessions see it.
  $claimArgs = @("scripts/tasks.py", "claim", "local"); if ($ForceLock) { $claimArgs += "--force" }
  $prevE = $ErrorActionPreference; $ErrorActionPreference = "Continue"
  $claimOut = Invoke-Py $claimArgs 2>&1 | Out-String
  $claimExit = $LASTEXITCODE; $ErrorActionPreference = $prevE
  if ($claimExit -eq 3) { Write-Host $claimOut -ForegroundColor Yellow; Write-Host "A cloud session is building. Re-run later or use -ForceLock." -ForegroundColor Yellow; break }
  git add docs/plan/tasks.json | Out-Null
  git commit -q -m "chore: builder lock (local)" 2>$null | Out-Null
  git push -q 2>$null | Out-Null
  $useModel = if ($Model -eq "auto") { $task.model } else { $Model }
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $log = Join-Path $logDir "$stamp-$($task.id).log"
  Write-Host "`n=== $($task.id) $($task.title)  [model: $useModel] ===" -ForegroundColor Cyan

  $beforeDone = Get-DoneCount; $beforeHead = Get-Head
  $claudeArgs = @("-p", $Prompt, "--model", $useModel, "--output-format", "text")
  # claude rejects a fallback model identical to the main model, so only pass it when different
  if ($FallbackModel -and $FallbackModel -ne $useModel) { $claudeArgs += @("--fallback-model", $FallbackModel) }
  if ($SkipPermissions) { $claudeArgs += "--dangerously-skip-permissions" } else { $claudeArgs += @("--permission-mode", "acceptEdits") }

  $output = ""
  $prevEap = $ErrorActionPreference; $ErrorActionPreference = "Continue"
  try {
    # UTF-8 log (Tee-Object writes UTF-16 on Windows PowerShell 5.1)
    & claude @claudeArgs 2>&1 | ForEach-Object { $line = "$_"; Write-Host $line; $output += "$line`n"; [IO.File]::AppendAllText($log, "$line`n", [Text.UTF8Encoding]::new($false)) }
  } catch {
    $output += "`n$($_.Exception.Message)"
  }
  $exit = $LASTEXITCODE
  $ErrorActionPreference = $prevEap

  $afterDone = Get-DoneCount; $afterHead = Get-Head
  $completed = $output -match "TASK_COMPLETE\s+$($task.id)"
  $blocked = $output -match "TASK_BLOCKED"
  $continued = $output -match "TASK_CONTINUE\s+$($task.id)"

  if ($completed -or $afterDone -gt $beforeDone) {
    Write-Host "Completed $($task.id)." -ForegroundColor Green
    $noProgress = 0
    if ($Once -or ($StopAt -and $task.id -eq $StopAt)) { break }
    if ($PauseAfter -ne "none" -and -not (Request-Continue "Task $($task.id) done")) { break }
    continue
  }
  if ($output -match "TASK_BUSY") { Write-Host "Another builder holds the lock - stopping." -ForegroundColor Yellow; break }
  if ($blocked) { Write-Host "Task blocked - see docs/plan/PROGRESS.md." -ForegroundColor Yellow; break }
  if ($continued -and $output -notmatch '(?i)(session limit|hit your|usage limit)') {
    Write-Host "Step budget used; continuing $($task.id) in a fresh session." -ForegroundColor DarkCyan
    $noProgress = 0
    if ($PauseAfter -eq "session" -and -not (Request-Continue "Session for $($task.id) finished")) { break }
    continue
  }

  $wait = Get-LimitWaitSeconds $output
  if ($wait -gt 0) {
    if (-not $WaitOnLimit) { Write-Host "Usage limit hit. Re-run later; progress is checkpointed." -ForegroundColor Yellow; break }
    $until = (Get-Date).AddSeconds($wait)
    Write-Host "Usage/rate limit detected. Sleeping until $($until.ToString('HH:mm')) then resuming $($task.id)..." -ForegroundColor Yellow
    # Wall-clock wait in 1-minute ticks: a single long Start-Sleep does not count time while the
    # laptop is suspended, so after sleep/hibernate the loop would keep waiting for hours.
    # Tip: keep the PC awake overnight (powercfg /change standby-timeout-ac 0) for unattended runs.
    while ((Get-Date) -lt $until) { Start-Sleep -Seconds 60 }
    continue
  }

  if ($afterHead -ne $beforeHead) {
    Write-Host "Session ended mid-task with checkpoints committed; resuming in a fresh session." -ForegroundColor Yellow
    $noProgress = 0
    if ($PauseAfter -eq "session" -and -not (Request-Continue "Session for $($task.id) finished")) { break }
    continue
  } else {
    $noProgress++
    Write-Host "No progress this iteration (exit $exit). $noProgress/$MaxNoProgress. Log: $log" -ForegroundColor Red
    if ($noProgress -ge $MaxNoProgress) { Write-Host "Stopping - inspect the log, then re-run." -ForegroundColor Red; break }
  }
  if ($Once) { break }
}
# Release the lock so cloud sessions can build.
$prevE = $ErrorActionPreference; $ErrorActionPreference = "Continue"
git pull --rebase --autostash -q 2>$null | Out-Null
Invoke-Py @("scripts/tasks.py", "release", "local") | Out-Null
git add docs/plan/tasks.json | Out-Null
git commit -q -m "chore: release builder lock (local)" 2>$null | Out-Null
git push -q 2>$null | Out-Null
$ErrorActionPreference = $prevE
Invoke-Py @("scripts/tasks.py", "status")
