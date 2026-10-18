"""OutputSettings: the [output] table of the config file."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from weblogstats.config import OutputSettings


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "weblogstats.toml"
    path.write_text(text, encoding="utf-8")
    return path


class TestOutputSettings:
    def test_defaults_set_no_errors_file(self) -> None:
        assert OutputSettings.defaults().errors_file is None

    def test_reads_errors_file(self, tmp_path: Path) -> None:
        path = _write(tmp_path, '[output]\nerrors_file = "logs/bad.log"\n')
        assert OutputSettings.load(path).errors_file == Path("logs/bad.log")

    def test_a_file_without_an_output_table_sets_nothing(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "[lookups.geoip]\ncache_size = 10\n")
        assert OutputSettings.load(path).errors_file is None

    def test_an_output_table_without_errors_file_sets_nothing(self, tmp_path: Path) -> None:
        assert OutputSettings.load(_write(tmp_path, "[output]\n")).errors_file is None

    @pytest.mark.parametrize("value", ['""', '"   "', "3", "true", '["a"]'])
    def test_a_bad_errors_file_is_rejected_naming_the_file_and_key(
        self, tmp_path: Path, value: str
    ) -> None:
        path = _write(tmp_path, f"[output]\nerrors_file = {value}\n")
        with pytest.raises(ValueError) as error:
            OutputSettings.load(path)
        assert str(path) in str(error.value)
        assert "output.errors_file" in str(error.value)

    def test_an_unknown_key_in_output_is_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, '[output]\nerror_file = "x.log"\n')
        with pytest.raises(ValueError) as error:
            OutputSettings.load(path)
        assert str(path) in str(error.value)
        assert "output.error_file" in str(error.value)

    def test_output_that_is_not_a_table_is_rejected(self, tmp_path: Path) -> None:
        path = _write(tmp_path, 'output = "x.log"\n')
        with pytest.raises(ValueError) as error:
            OutputSettings.load(path)
        assert str(path) in str(error.value)
        assert "'output' must be a table" in str(error.value)

    def test_invalid_toml_is_a_value_error_naming_the_file(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "[output\n")
        with pytest.raises(ValueError, match="invalid TOML") as error:
            OutputSettings.load(path)
        assert str(path) in str(error.value)

    def test_a_missing_file_is_file_not_found_naming_the_path(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="nope.toml"):
            OutputSettings.load(tmp_path / "nope.toml")

    def test_the_settings_are_immutable(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            OutputSettings.defaults().errors_file = Path("x")  # type: ignore[misc]

    def test_the_shipped_config_file_sets_the_default_errors_file(self) -> None:
        shipped = Path(__file__).resolve().parents[2] / "config" / "weblogstats.toml"
        assert OutputSettings.load(shipped).errors_file == Path("weblogstats-errors.log")
