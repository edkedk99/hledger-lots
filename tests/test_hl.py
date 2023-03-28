from io import StringIO
from pathlib import Path
from sys import setprofile

import pytest
from _pytest.tmpdir import tmp_path_factory

from hledger_fifo import hl
from hledger_fifo.lib import AdjustedTxn, Txn

from . import lots_data


class TestTxn2Hl:
    txns = lots_data.expected_qtty_reaches_zero_sell_all
    date = "2022-02-01"
    cash_account = "Bank"
    revenue_account = "Revenue"

    def test_txn2hl_profit(self):
        cur = "USD"
        test = hl.txn2hl(
            self.txns, self.date, cur, self.cash_account, self.revenue_account, 160
        )

        expected = """2022-02-01 Sold USD
    ; commodity:USD, qtty:5.00, price:32.00
    ; avg_fifo_cost:26.0000, xirr:61.42% annual percent rate 30/360US
    Bank                 160.00 USD
    Acct1      -2.00 USD @ 35.0 USD  ; buy_date:2022-01-12, base_cur:USD
    Acct1      -3.00 USD @ 20.0 USD  ; buy_date:2022-01-14, base_cur:USD
    Revenue              -30.00 USD

"""

        assert test == expected

    def test_txn2hl_loss(self):
        cur = "USD"
        test = hl.txn2hl(
            self.txns, self.date, cur, self.cash_account, self.revenue_account, 80
        )

        expected = """2022-02-01 Sold USD
    ; commodity:USD, qtty:5.00, price:32.00
    ; avg_fifo_cost:26.0000, xirr:61.42% annual percent rate 30/360US
    Bank                  80.00 USD
    Acct1      -2.00 USD @ 35.0 USD  ; buy_date:2022-01-12, base_cur:USD
    Acct1      -3.00 USD @ 20.0 USD  ; buy_date:2022-01-14, base_cur:USD
    Revenue              -50.00 USD

"""


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
        assert hl.adjust_txn(txn) == expected

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
        assert hl.adjust_txn(txn) == expected

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
            hl.adjust_txn(txn)


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

        assert hl.hledger2txn(file_tup, "AAPL") == expected

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

        assert hl.hledger2txn(file_tup, "BRL") == expected
