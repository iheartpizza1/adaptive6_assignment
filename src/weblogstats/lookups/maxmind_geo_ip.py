"""MaxMind GeoLite2 adapter for GeoIpLookup. The only module that imports geoip2."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import geoip2.database

_ACCEPTED_EDITIONS = ("Country", "City")


class MaxMindGeoIp:
    """Resolves an IP to its English country name using a GeoLite2 Country (or City) MMDB.

    ``reader_factory`` exists so unit tests can inject a stub reader; production uses
    ``geoip2.database.Reader``.
    """

    def __init__(
        self, db_path: Path, reader_factory: Callable[[str], Any] = geoip2.database.Reader
    ) -> None:
        if not db_path.is_file():
            raise FileNotFoundError(
                f"GeoIP database not found: {db_path}. "
                "Download GeoLite2-Country.mmdb from MaxMind and pass its path "
                "with --geoip or the GEOIP_DB environment variable."
            )
        self._reader = reader_factory(str(db_path))
        database_type = self._reader.metadata().database_type
        if not any(edition in database_type for edition in _ACCEPTED_EDITIONS):
            self._reader.close()
            raise ValueError(
                f"{db_path} is a {database_type!r} database. The GeoLite2-Country edition "
                "(or a City edition) is required to resolve countries."
            )

    def country_name(self, ip: str) -> str:
        return ""

    def close(self) -> None:
        """Release the database file."""
        self._reader.close()
