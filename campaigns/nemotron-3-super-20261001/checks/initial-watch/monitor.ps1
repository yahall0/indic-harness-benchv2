$ErrorActionPreference = 'Stop'
$taskCampaign = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskRoot = Split-Path -Parent (Split-Path -Parent $taskCampaign)
$taskPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath $taskRoot
while ($true) {
    # Clear the PowerShell console buffer even when native Python stdout is piped.
    Clear-Host
    # Clear terminal scrollback as well as the current screen on VT terminals.
    Write-Host -NoNewline "$([char]27)[3J$([char]27)[2J$([char]27)[H"
    if (Test-Path -LiteralPath (Join-Path $taskCampaign 'results\STOP_REQUESTED')) {
        Write-Host 'CAMPAIGN ON HOLD - infrastructure review; saved attempts are preserved.' -ForegroundColor Yellow
    }
    & $taskPython -B -X utf8 (Join-Path $PSScriptRoot 'compact_monitor.py')
    Start-Sleep -Seconds 5
}
