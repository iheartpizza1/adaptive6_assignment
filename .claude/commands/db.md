---
description: Start, stop, or check the local MySQL (geoip) database
argument-hint: start | stop | status
allowed-tools: Bash(powershell:*), PowerShell
---

Manage the local MySQL server that hosts the `geoip` database by running
`db/server.ps1` with the action from the arguments: `$ARGUMENTS`.

- Valid actions are `start`, `stop`, `status`. If the argument is empty, use `status`.
- Run: `powershell -NoProfile -File db/server.ps1 <action>`
- Report the script's output in one line. Do not modify the script or the data directory.
