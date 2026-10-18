# Builds the geoip MySQL database from the GeoLite2-Country CSV zip in the repo root.
# usage: .\db\setup.ps1 [-MysqlBin 'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe'] [-User root]
# Password is read from the MYSQL_PWD environment variable.
param(
  [string]$MysqlBin = 'mysql',
  [string]$User = 'root',
  [string]$Zip = (Join-Path $PSScriptRoot '..\GeoLite2-Country-CSV_20261016.zip')
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$gen = Join-Path $PSScriptRoot 'generated'
$stage = Join-Path $gen 'extracted'
New-Item -ItemType Directory -Force $gen | Out-Null
Expand-Archive -Force $Zip $stage
$src = (Get-ChildItem $stage -Directory | Select-Object -First 1).FullName
foreach ($v in 'IPv4', 'IPv6') {
  python -I scripts/convert_blocks.py "$src\GeoLite2-Country-Blocks-$v.csv" "$gen\GeoLite2-Country-Blocks-$v-Hex.csv"
}
Copy-Item "$src\GeoLite2-Country-Locations-en.csv" $gen -Force
Get-Content schema.sql -Raw | & $MysqlBin -u $User --local-infile=1
Get-Content load.sql -Raw | & $MysqlBin -u $User --local-infile=1 geoip
