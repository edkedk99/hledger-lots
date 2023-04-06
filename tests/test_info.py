from datetime import date, datetime
from pathlib import Path
from typing import Tuple

import pytest

from hledger_lots.fifo_info import FifoInfo
from hledger_lots.avg_info import AvgInfo
import sys



def price_journal(price: str):
    prices = f"""
P 2023-01-05 AAPL 25 USD
P 2023-01-20 AAPL 25 USD
P 2023-02-01 AAPL {price}
"""
    return prices


price_tests = [
    (price_journal("35 USD"), 35),
    (price_journal("35USD"), 35),
    (price_journal("USD 35"), 35),
    (price_journal("USD35"), 35),
]


@pytest.fixture()
def journals(tmp_path: Path):
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

    hl_txns += price_journal("6 USD")
    file_path = tmp_path.joinpath("data.journal")
    file_path.touch()
    file_path.write_text(hl_txns)
    file_tup = (str(file_path),)
    return file_tup


@pytest.fixture()
def fifo_info(journals: Tuple[str, ...], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "stdin", None)
    return FifoInfo(journals, "AAPL", False)

@pytest.fixture()
def avg_info(journals: Tuple[str, ...], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "stdin", None)
    return AvgInfo(journals, "AAPL", False)



class TestInfo:
    @pytest.mark.parametrize("journal,expected", price_tests)
    def test_last_price(
        self,
        tmp_path: Path,
        journal: str,
        expected: float,
        monkeypatch: pytest.MonkeyPatch,
    ):
        file_path = tmp_path.joinpath("data.journal")
        file_path.touch()
        file_path.write_text(journal)
        file_tup = (str(file_path),)

        monkeypatch.setattr(sys, "stdin", None)
        fifo_info = FifoInfo(file_tup, "AAPL", False)

        assert fifo_info.last_price == (date(2023, 2, 1), expected)

    def test_lots_xirr(self, fifo_info: FifoInfo):
        last_buy_date_str = fifo_info.last_buy_date
        if not last_buy_date_str:
            raise ValueError("last_buy_date is None")
        else:
            last_buy_date = datetime.strptime(last_buy_date_str, "%Y-%m-%d").date()

            assert fifo_info.get_lots_xirr(last_buy_date) == pytest.approx(
                6.2528, abs=0.0001
            )


class TestLotInfo:
    expected = {
            "comm": "AAPL",
            "cur": "USD",
            "qtty": "6",
            "amount": "31.20",
            "avg_cost": "5.2000",
            "mkt_price": "6.0000",
            "mkt_amount": "36.00",
            "mkt_profit": "4.80",
            "mkt_date": "2023-02-01",
            "xirr": "6.2529%",
        }
    def test_fifo_info(self, fifo_info: FifoInfo):
        assert fifo_info.info == self.expected

    def test_avg_info(self, avg_info: AvgInfo):
        assert avg_info.info == self.expected

    
