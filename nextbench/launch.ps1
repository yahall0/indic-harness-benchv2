param([switch]$LaunchAuthorized)
$ErrorActionPreference = 'Stop'
if (-not $LaunchAuthorized) { throw 'Benchmark launch requires the user to authorize start. Preparation does not authorize launch.' }
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskCampaign = Join-Path $taskRoot 'campaigns\nemotron-3-super-20261001'
$taskPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Push-Location -LiteralPath $taskRoot
try {
    $taskReadyText = & $taskPython -B -X utf8 -m nextbench.runner ready $taskCampaign
    if ($LASTEXITCODE -ne 0) { throw 'Readiness verification failed.' }
    $taskReady = $taskReadyText | ConvertFrom-Json
    if (-not $taskReady.ready) { throw ('Launch blocked: ' + ($taskReady.blocking_gates -join ', ')) }
    $taskStamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
    $taskLog = Join-Path $taskCampaign ('results\logs\' + $taskStamp)
    New-Item -ItemType Directory -Path $taskLog -Force | Out-Null
    $taskControllerArgs = '-B -X utf8 -m nextbench.runner start "' + $taskCampaign + '" --launch-authorized'
    $taskController = Start-Process -FilePath $taskPython -ArgumentList $taskControllerArgs -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLog 'controller.stdout.log') -RedirectStandardError (Join-Path $taskLog 'controller.stderr.log') -PassThru
    $taskMonitorCommand = '& ''' + $taskPython + ''' -B -X utf8 -m nextbench.monitor ''' + $taskCampaign + ''''
    $taskMonitorArgs = '-NoProfile -NoExit -Command "' + $taskMonitorCommand + '"'
    $taskMonitor = Start-Process -FilePath 'powershell.exe' -ArgumentList $taskMonitorArgs -WorkingDirectory $taskRoot -WindowStyle Normal -PassThru
    [ordered]@{controller_process_id=$taskController.Id; monitor_process_id=$taskMonitor.Id; log_directory=$taskLog; requested_utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskLog 'launch.json') -Encoding UTF8
    Write-Output ('Controller launched under exclusive locks. Logs: ' + $taskLog)
    Write-Output 'The visible read-only monitor can be closed independently. Stop the campaign using python -m nextbench.stop <campaign>.'
}
finally { Pop-Location }
