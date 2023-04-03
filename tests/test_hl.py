from pathlib import Path

import pytest

from hledger_lots.lib import AdjustedTxn, Txn
from hledger_lots.hl import adjust_txn, hledger2txn

from . import lots_data


class TestAdjustTxn:
    def test_adjust_txn_unit_price(self):
        txn = Txn(
            date="2022-01-01",
            price=10.0,
            base_cur="USD",
            qtty=1.0,
            acct="Acct1",
            type="UnitPrice",
        )
        expected = AdjustedTxn(
            date="2022-01-01", price=10.0, base_cur="USD", qtty=1.0, acct="Acct1"
        )
        assert adjust_txn(txn) == expected

    def test_adjust_txn_total_price(self):
        txn = Txn(
            date="2022-01-01",
            price=20.0,
            base_cur="USD",
            qtty=2.0,
            acct="Acct1",
            type="TotalPrice",
        )
        expected = AdjustedTxn(
            date="2022-01-01", price=10.0, base_cur="USD", qtty=2.0, acct="Acct1"
        )
        assert adjust_txn(txn) == expected

    def test_adjust_txn_zero_quantity(self):
        txn = Txn(
            date="2022-01-01",
            price=10.0,
            base_cur="USD",
            qtty=0.0,
            acct="Acct1",
            type="TotalPrice",
        )
        with pytest.raises(ZeroDivisionError):
            adjust_txn(txn)


class TestHledger2Txn:
    hl_txns = """2023-01-05 Buy AAPL
    Asset:Stocks                                   3 AAPL @ 5.2 USD
    Asset:Bank

2023-01-10 Buy BRL
    Asset:FOREX                                  55 BRL @@ 10 USD
    Asset:Bank

2023-01-05 Sell AAPL
    Asset:Bank                                    20 BRL
    Asset:Stocks                                   3 AAPL @ 5.2 USD
    Revenue:Capital Gain
"""

    def test_price_qtty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        expected = [
            AdjustedTxn(
                date="2023-01-05",
                price=5.2,
                base_cur="USD",
                qtty=3,
                acct="Asset:Stocks",
            ),
            AdjustedTxn(
                date="2023-01-05",
                price=5.2,
                base_cur="USD",
                qtty=3,
                acct="Asset:Stocks",
            ),
        ]

        monkeypatch.setattr("sys.stdin", None)

        file_path = tmp_path.joinpath("data.journal")
        file_path.touch()
        file_path.write_text(self.hl_txns)
        file_tup = (str(file_path),)

        assert hledger2txn(file_tup, "AAPL") == expected

    def test_total_amount(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        expected = [
            AdjustedTxn(
                date="2023-01-10",
                price= 10/55,
                base_cur="USD",
                qtty=55,
                acct="Asset:FOREX",
            )
        ]

        monkeypatch.setattr("sys.stdin", None)

        file_path = tmp_path.joinpath("data.journal")
        file_path.touch()
        file_path.write_text(self.hl_txns)
        file_tup = (str(file_path),)

        assert hledger2txn(file_tup, "BRL") == expected
