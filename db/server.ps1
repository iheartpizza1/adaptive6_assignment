# Start/stop/status for the local MySQL server that hosts the geoip database.
# usage: .\db\server.ps1 start|stop|status
param(
  [Parameter(Mandatory)][ValidateSet('start', 'stop', 'status')][string]$Action,
  [string]$MysqlDir = 'C:\Program Files\MySQL\MySQL Server 8.4',
  [string]$DataDir = (Join-Path $env:USERPROFILE 'mysql-data')
)
$ErrorActionPreference = 'Stop'
$mysqld = Join-Path $MysqlDir 'bin\mysqld.exe'
$admin = Join-Path $MysqlDir 'bin\mysqladmin.exe'

function Test-Up {
  # mysqladmin writes to stderr when the server is down; don't let that become a terminating error.
  $ErrorActionPreference = 'Continue'
  & $admin -u root --connect-timeout=2 ping *> $null
  $LASTEXITCODE -eq 0
}

switch ($Action) {
  'status' {
    if (Test-Up) { 'MySQL is running on 127.0.0.1:3306' } else { 'MySQL is stopped' }
  }
  'start' {
    if (Test-Up) { 'MySQL is already running'; return }
    Start-Process -FilePath $mysqld -WindowStyle Hidden -ArgumentList `
      "--datadir=$DataDir", '--bind-address=127.0.0.1', '--local-infile=1', '--port=3306'
    for ($i = 0; $i -lt 30 -and -not (Test-Up); $i++) { Start-Sleep 1 }
    if (Test-Up) { 'MySQL started on 127.0.0.1:3306' } else { throw 'MySQL did not come up within 30s' }
  }
  'stop' {
    if (-not (Test-Up)) { 'MySQL is already stopped'; return }
    & $admin -u root shutdown
    'MySQL stopped'
  }
}
