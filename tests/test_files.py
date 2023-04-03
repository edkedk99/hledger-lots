import pytest
from hledger_lots import files
import click


class PathMissing:
    @staticmethod
    def exists():
        return False


class TestGetDefaultFile:
    def test_with_file_env(self, monkeypatch: pytest.MonkeyPatch):
        file_env = "/path/to/file.dat"
        monkeypatch.setenv("LEDGER_FILE", file_env)
        assert files.get_default_file() == (file_env,)

    def test_with_default_path(self, monkeypatch, tmp_path):
        default_path = tmp_path.home() / ".hledger.journal"
        monkeypatch.setattr("hledger_lots.files.default_path", default_path)
        assert files.get_default_file() == (str(default_path),)

    def test_missing_file(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("LEDGER_FILE", raising=False)
        monkeypatch.setattr("hledger_lots.files.default_path", PathMissing())

        with pytest.raises(click.BadOptionUsage):
            files.get_default_file()


class TestGetFilePath:
    def test_has_value(self):
        value = ("a.journal", "b.journal")
        context = click.Context(click.Command("command"))
        assert files.get_file_path(context, None, value) == value

    def test_no_parent(self):
        context = click.Context(click.Command("command"))
        assert files.get_file_path(context, None, None) is None

    def test_get_parent(self):
        default_file = ("default.journal",)
        parent = click.Context(click.Command("parent"))
        parent.params = dict(file=default_file)
        context = click.Context(click.Command("command"), parent=parent)
        assert files.get_file_path(context, None, None) == default_file


class TestGetFilesComm:
    def test_empty_path(self):
        assert files.get_files_comm(tuple()) == []

    def test_single_file(self):
        assert files.get_files_comm(("file1.txt",)) == ["-f", "file1.txt"]

    def test_multiple_files(self):
        assert files.get_files_comm(("file1.txt", "file2.txt", "file3.txt")) == [
            "-f",
            "file1.txt",
            "-f",
            "file2.txt",
            "-f",
            "file3.txt",
        ]

    def test_duplicate_files(self):
        assert files.get_files_comm(("file1.txt", "file1.txt")) == [
            "-f",
            "file1.txt",
            "-f",
            "file1.txt",
        ]
