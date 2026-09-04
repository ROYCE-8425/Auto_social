# Dung Javis OS - giet theo python cua repo va chu port 7777
$killed = $false

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  ($_.Name -like 'python*.exe') -and ($_.CommandLine -like '*server\main.py*' -or $_.CommandLine -like '*javis-os*')
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  Write-Host "  - Da tat python PID $($_.ProcessId)"
  $killed = $true
}

# Phong ho: ai dang giu port 7777
Get-NetTCPConnection -LocalPort 7777 -ErrorAction SilentlyContinue | ForEach-Object {
  if ($_.OwningProcess -gt 0) {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "  - Da tat PID $($_.OwningProcess) (chu port 7777)"
    $killed = $true
  }
}

if (-not $killed) { Write-Host '  (Khong thay server nao dang chay)' }
exit 0

