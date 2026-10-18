"""Per-lookup settings read from a TOML file."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_CACHE_SIZE = "cache_size"
# Keys a [lookups.<name>] table may hold. A typo is an error rather than a silent default.
_KNOWN_KEYS = frozenset({_CACHE_SIZE})


@dataclass(frozen=True)
class LookupSettings:
    """Settings per lookup name, e.g. ``{"geoip": {"cache_size": 3506}}``.

    The mapping is generic on purpose: a new lookup adds a ``[lookups.<name>]`` table to the file
    and one ``cache_size(...)`` call where it is built, and nothing changes here.
    """

    lookups: Mapping[str, Mapping[str, int]] = field(default_factory=dict)

    @classmethod
    def defaults(cls) -> LookupSettings:
        """No settings: every lookup uses its own constructor default."""
        return cls()

    @classmethod
    def load(cls, path: Path) -> LookupSettings:
        """Read ``[lookups.*]`` from a TOML file.

        Raises FileNotFoundError for a missing file and ValueError, naming the file and the key,
        for invalid TOML or invalid values. An unknown lookup *name* is allowed.
        """
        if not path.is_file():
            raise FileNotFoundError(f"config file not found: {path}")
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{path}: invalid TOML: {error}") from error
        return cls(_parse_lookups(data.get("lookups", {}), path))

    def cache_size(self, lookup: str, default: int) -> int:
        """The configured cache size for ``lookup``, or ``default`` when it has none."""
        return self.lookups.get(lookup, {}).get(_CACHE_SIZE, default)


def _parse_lookups(raw: object, path: Path) -> dict[str, dict[str, int]]:
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: 'lookups' must be a table, got {raw!r}")
    return {name: _parse_lookup(name, table, path) for name, table in raw.items()}


def _parse_lookup(name: str, table: object, path: Path) -> dict[str, int]:
    if not isinstance(table, dict):
        raise ValueError(f"{path}: lookups.{name} must be a table, got {table!r}")
    for key in table:
        if key not in _KNOWN_KEYS:
            known = ", ".join(sorted(_KNOWN_KEYS))
            raise ValueError(f"{path}: unknown key lookups.{name}.{key} (known keys: {known})")
    settings: dict[str, int] = {}
    if _CACHE_SIZE in table:
        value = table[_CACHE_SIZE]
        # bool is an int subclass in Python, so it is rejected explicitly.
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"{path}: lookups.{name}.{_CACHE_SIZE} must be an integer >= 1, got {value!r}"
            )
        settings[_CACHE_SIZE] = value
    return settings
