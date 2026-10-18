"""Output settings read from the [output] table of the TOML config file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

_ERRORS_FILE = "errors_file"
# Keys the [output] table may hold. A typo is an error rather than a silent default.
_KNOWN_KEYS = frozenset({_ERRORS_FILE})


@dataclass(frozen=True)
class OutputSettings:
    """Where the run writes its side files. ``errors_file`` is None when the file does not set it.

    A relative ``errors_file`` is relative to the current directory, like the ``--errors-file``
    flag, not to the config file.
    """

    errors_file: Path | None = None

    @classmethod
    def defaults(cls) -> OutputSettings:
        """No settings: the CLI falls back to its own defaults."""
        return cls()

    @classmethod
    def load(cls, path: Path) -> OutputSettings:
        """Read ``[output]`` from a TOML file; other tables are ignored.

        Raises FileNotFoundError for a missing file and ValueError, naming the file and the key,
        for invalid TOML or invalid values.
        """
        if not path.is_file():
            raise FileNotFoundError(f"config file not found: {path}")
        try:
            with path.open("rb") as handle:
                data = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{path}: invalid TOML: {error}") from error
        table = data.get("output", {})
        if not isinstance(table, dict):
            raise ValueError(f"{path}: 'output' must be a table, got {table!r}")
        for key in table:
            if key not in _KNOWN_KEYS:
                known = ", ".join(sorted(_KNOWN_KEYS))
                raise ValueError(f"{path}: unknown key output.{key} (known keys: {known})")
        if _ERRORS_FILE not in table:
            return cls()
        value = table[_ERRORS_FILE]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{path}: output.{_ERRORS_FILE} must be a non-empty string path, got {value!r}"
            )
        return cls(errors_file=Path(value))
