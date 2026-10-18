from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from weblogstats.contracts import LogSource
from weblogstats.sources.file_log_source import FileLogSource


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


class TestFileLogSource:
    def test_satisfies_the_log_source_protocol(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", b"x\n")
        assert isinstance(FileLogSource(path), LogSource)

    def test_streams_lazily(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", b"one\ntwo\nthree\n")
        iterator = FileLogSource(path).lines()
        assert inspect.isgenerator(iterator)
        assert next(iterator) == "one"
        # The file is not exhausted: the generator is suspended mid-file.
        assert inspect.getgeneratorstate(iterator) == inspect.GEN_SUSPENDED
        assert list(iterator) == ["two", "three"]

    def test_strips_lf_and_crlf(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", b"lf\ncrlf\r\nlast")
        assert list(FileLogSource(path).lines()) == ["lf", "crlf", "last"]

    def test_decodes_utf_8_and_replaces_invalid_bytes(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", "café\n".encode() + b"bad \xff\xfe byte\n")
        assert list(FileLogSource(path).lines()) == ["café", "bad �� byte"]

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", b"a\n\n   \n\t\r\nb\n")
        assert list(FileLogSource(path).lines()) == ["a", "b"]

    def test_keeps_inner_whitespace_and_trailing_spaces_of_content_lines(
        self, tmp_path: Path
    ) -> None:
        path = _write(tmp_path / "a.log", b"a  b \n")
        assert list(FileLogSource(path).lines()) == ["a  b "]

    def test_sample_log_has_19_non_blank_lines(self, sample_log_path: Path) -> None:
        assert len(list(FileLogSource(sample_log_path).lines())) == 19

    def test_missing_file_raises_from_the_constructor(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            FileLogSource(tmp_path / "missing.log")

    def test_a_lone_carriage_return_inside_a_line_is_kept(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "a.log", b"a\rb\tc\n")
        assert list(FileLogSource(path).lines()) == ["a\rb\tc"]
