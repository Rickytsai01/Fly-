Option Explicit
Dim shell, fso, root, ps1, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
ps1 = "& { $p = Join-Path " + Chr(34) + root + Chr(34) + " '.flightsim_server.pid'; if (Test-Path -LiteralPath $p) { $raw = Get-Content -LiteralPath $p -ErrorAction SilentlyContinue; if ($raw -match '^\d+$') { Stop-Process -Id ([int]$raw) -Force -ErrorAction SilentlyContinue }; Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue } }"
command = "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & Chr(34) & ps1 & Chr(34)
shell.Run command, 0, False
