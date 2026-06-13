<#
.SYNOPSIS
  Înregistrează (sau elimină) un task zilnic Windows care rulează scanner-ul.

.EXEMPLE
  # zilnic la 03:00 (implicit)
  powershell -ExecutionPolicy Bypass -File scripts\install_task_windows.ps1

  # altă oră
  powershell -ExecutionPolicy Bypass -File scripts\install_task_windows.ps1 -Time 06:30

  # eliminare
  powershell -ExecutionPolicy Bypass -File scripts\install_task_windows.ps1 -Uninstall

  Logul rulărilor: data\scan.log
#>
param(
  [string]$Time = "03:00",
  [string]$TaskName = "PortalActiuniColective-Scan",
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot
$py = Join-Path $proj ".venv\Scripts\python.exe"
$script = Join-Path $proj "scripts\run_scanner.py"
$log = Join-Path $proj "data\scan.log"

if ($Uninstall) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Task '$TaskName' eliminat."
  return
}

if (-not (Test-Path $py)) { throw "Nu găsesc venv-ul: $py. Rulează întâi setup-ul (vezi README)." }

# rulăm prin powershell ca să putem redirecta stdout+stderr în log
$cmd = "& '$py' '$script' *>> '$log'"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`"" `
  -WorkingDirectory $proj
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
  -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Settings $settings -Description "Scanează portal.just.ro pentru acțiuni colective" -Force | Out-Null

Write-Host "Task '$TaskName' înregistrat — rulează zilnic la $Time."
Write-Host "Log: $log"
Write-Host "Verifică: Get-ScheduledTask -TaskName $TaskName"
