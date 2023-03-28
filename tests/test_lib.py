from hledger_fifo import lib
from hledger_fifo.lib import AdjustedTxn, get_file_path
import pytest
import click
from datetime import date
import pyxirr


class TestGetAvg:
    def test_empty_list(self):
        assert lib.get_avg([]) == 0

    def test_single_txn(self):
        txn = AdjustedTxn(
            date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
        )
        assert lib.get_avg([txn]) == 100.0

    def test_multiple_txns(self):
        txns = [
            AdjustedTxn(
                date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-02", price=150.0, base_cur="USD", qtty=5.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-03", price=200.0, base_cur="USD", qtty=20.0, acct="1234"
            ),
        ]
        assert lib.get_avg(txns) == pytest.approx(164.28, abs=1e-2)

    def test_zero_quantity(self):
        txns = [
            AdjustedTxn(
                date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-02", price=150.0, base_cur="USD", qtty=0.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-03", price=200.0, base_cur="USD", qtty=20.0, acct="1234"
            ),
        ]
        assert lib.get_avg(txns) == pytest.approx(166.67, abs=1e-2)


class PathMissing:
    @staticmethod
    def exists():
        return False


class TestGetDefaultFile:
    def test_with_file_env(self, monkeypatch: pytest.MonkeyPatch):
        file_env = "/path/to/file.dat"
        monkeypatch.setenv("LEDGER_FILE", file_env)
        assert lib.get_default_file() == (file_env,)

    def test_with_default_path(self, monkeypatch, tmp_path):
        default_path = tmp_path.home() / ".hledger.journal"
        monkeypatch.setattr("hledger_fifo.lib.default_path", default_path)
        assert lib.get_default_file() == (str(default_path),)

    def test_missing_file(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("LEDGER_FILE", raising=False)
        monkeypatch.setattr("hledger_fifo.lib.default_path", PathMissing())

        with pytest.raises(click.BadOptionUsage):
            lib.get_default_file()


class TestGetFilePath:
    def test_has_value(self):
        value = ("a.journal", "b.journal")
        context = click.Context(click.Command("command"))
        assert get_file_path(context, None, value) == value

    def test_no_parent(self):
        context = click.Context(click.Command("command"))
        assert get_file_path(context, None, None) is None

    def test_get_parent(self):
        default_file = ("default.journal",)
        parent = click.Context(click.Command("parent"))
        parent.params = dict(file=default_file)
        context = click.Context(click.Command("command"), parent=parent)
        assert get_file_path(context, None, None) == default_file


class TestGetFilesComm:
    def test_empty_path(self):
        assert lib.get_files_comm(tuple()) == []

    def test_single_file(self):
        assert lib.get_files_comm(("file1.txt",)) == ["-f", "file1.txt"]

    def test_multiple_files(self):
        assert lib.get_files_comm(("file1.txt", "file2.txt", "file3.txt")) == [
            "-f",
            "file1.txt",
            "-f",
            "file2.txt",
            "-f",
            "file3.txt",
        ]

    def test_duplicate_files(self):
        assert lib.get_files_comm(("file1.txt", "file1.txt")) == [
            "-f",
            "file1.txt",
            "-f",
            "file1.txt",
        ]


class TestGetXirr:
    txns = [
            AdjustedTxn("2023-01-23", 100, "USD", -1, "acct"),
            AdjustedTxn("2023-02-23", 100, "USD", -1, "acct"),
        ]
    
    def test_xirr_ok(self):
        assert lib.get_xirr(101,date(2023,3,23),self.txns) == pytest.approx(0.0828, abs=1e-4)

    def test_xirr_only_negatives(self):
        with pytest.raises(pyxirr.InvalidPaymentsError):
            lib.get_xirr(0,date(2023,3,23),self.txns)

    def test_xirr_empty(self):
        with pytest.raises(pyxirr.InvalidPaymentsError):
            lib.get_xirr(0,date(2023,3,23),[])

    def test_xir_negative(self):
        assert lib.get_xirr(99,date(2023,3,23),self.txns) == pytest.approx(-0.0772, abs=1e-4)
        


        
        
