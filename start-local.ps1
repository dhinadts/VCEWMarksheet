$ErrorActionPreference = "Stop"

$marksheetFrontendProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*D:\marksheets\frontend*" -and
    ($_.CommandLine -like "*next*dev*" -or $_.CommandLine -like "*start-server.js*")
}
$marksheetFrontendProcesses | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
$marksheetBackendListener = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
if ($marksheetBackendListener) {
    Stop-Process -Id $marksheetBackendListener.OwningProcess -Force -ErrorAction SilentlyContinue
}

$backendEnvironment = [System.Environment]::GetEnvironmentVariables()
Start-Process -FilePath "D:\marksheets\backend\venv\Scripts\python.exe" `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001") `
    -WorkingDirectory "D:\marksheets\backend" `
    -RedirectStandardOutput "D:\marksheets\backend\uvicorn.stdout.log" `
    -RedirectStandardError "D:\marksheets\backend\uvicorn.stderr.log" `
    -WindowStyle Hidden

$previousBackendUrl = [System.Environment]::GetEnvironmentVariable("BACKEND_API_URL", "Process")
[System.Environment]::SetEnvironmentVariable("BACKEND_API_URL", "http://127.0.0.1:8001/api/v1", "Process")
Start-Process -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "-H", "127.0.0.1", "-p", "3001") `
    -WorkingDirectory "D:\marksheets\frontend" `
    -RedirectStandardOutput "D:\marksheets\frontend\next.stdout.log" `
    -RedirectStandardError "D:\marksheets\frontend\next.stderr.log" `
    -WindowStyle Hidden
[System.Environment]::SetEnvironmentVariable("BACKEND_API_URL", $previousBackendUrl, "Process")

Start-Sleep -Seconds 6
Get-NetTCPConnection -LocalPort 8001, 3001 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess |
    Sort-Object LocalPort
