# adaptive6_assignment

Home Assignment from Adaptive6.

## GeoIP database (MySQL)

IP → country lookups run against a local MySQL 8.4 database named `geoip`, built from the
MaxMind GeoLite2 **Country** CSVs following
[MaxMind's MySQL import guide](https://dev.maxmind.com/geoip/importing-databases/mysql/)
(adapted from the City columns it shows to the Country ones).

### Prerequisites

- MySQL Server 8.4 (`winget install Oracle.MySQL`), installed at `C:\Program Files\MySQL\MySQL Server 8.4`
- Python 3 (used by the CIDR → hex-range converter)
- `GeoLite2-Country-CSV_<date>.zip` in the repo root (update the default `-Zip` path in `db/setup.ps1` if the date differs)

### One-time setup

The winget package installs the binaries but no service or data directory:

```powershell
$bin = 'C:\Program Files\MySQL\MySQL Server 8.4\bin'
& "$bin\mysqld.exe" --initialize-insecure --datadir="$env:USERPROFILE\mysql-data"   # root has an empty password
.\db\server.ps1 start
.\db\setup.ps1 -MysqlBin "$bin\mysql.exe"     # converts the CSVs, creates the schema, loads ~1M ranges
```

The server listens on `127.0.0.1:3306` only. `root` has no password, so this is for local development only.

### Start / stop

```powershell
.\db\server.ps1 start    # also: stop, status
```

In Claude Code the same thing is available as `/db start`, `/db stop` and `/db status`.
The server is a plain background process, not a Windows service, so start it again after a reboot.

### Looking up an IP

```powershell
mysql -u root geoip -e "SET @ip='8.8.8.8'; source db/lookup.sql"
```

or run [db/lookup.sql](db/lookup.sql) with the `@ip` of your choice. It works for IPv4 and IPv6 and returns no row for
private or unknown addresses. From application code, connect with `root@127.0.0.1:3306/geoip` and run the same query
with the IP as a parameter in place of `@ip`.

### Layout

| File | Purpose |
|---|---|
| `db/schema.sql` | Creates the `geoip` database and the `geoip2_network` / `geoip2_location` tables |
| `db/load.sql` | `LOAD DATA LOCAL INFILE` for the IPv4, IPv6 and English locations CSVs |
| `db/lookup.sql` | IP → country query |
| `db/scripts/convert_blocks.py` | CIDR → hex start/end converter (replaces MaxMind's `geoip2-csv-converter`) |
| `db/setup.ps1` | Rebuilds the database from the zip |
| `db/server.ps1` | Start / stop / status for the server |

Generated import files land in `db/generated/` (git-ignored).
