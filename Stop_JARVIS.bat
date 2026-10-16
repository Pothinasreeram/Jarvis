@echo off
echo Stopping all running J.A.R.V.I.S. instances...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo J.A.R.V.I.S. stopped successfully.
timeout /t 2 >nul
exit
