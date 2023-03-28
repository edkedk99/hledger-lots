from datetime import date
from pathlib import Path

import pytest

from hledger_fifo import lots_info
from hledger_fifo.lib import AdjustedTxn
from hledger_fifo.lots_info import LotInfo, LotsInfo

from . import lots_data


@pytest.fixture()
def journal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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

    file_path = tmp_path.joinpath("data.journal")
    file_path.touch()
    file_path.write_text(hl_txns)
    file_tup = (str(file_path),)
    return file_tup


@pytest.fixture()
def prices(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hl_txns = """
P 2022-01-05 AAPL 25 USD
P 2022-01-05 AAPL 25 USD
P 2022-01-05 AAPL 25 USD
    
"""

    file_path = tmp_path.joinpath("data.journal")
    file_path.touch()
    file_path.write_text(hl_txns)
    file_tup = (str(file_path),)
    return file_tup


def price_journal(price: str):
    prices = f"""
P 2022-01-05 AAPL 25 USD
P 2022-01-20 AAPL 25 USD
P 2022-02-01 AAPL {price}
"""
    return prices


price_tests = [
    (price_journal("35 USD"), 35),
    (price_journal("35USD"), 35),
    (price_journal("USD 35"), 35),
    (price_journal("USD35"), 35),
]


@pytest.fixture
def basic_lot_info(tmp_path: Path):
    prices = f"""
P 2022-01-05 AAPL 25 USD
P 2022-01-20 AAPL 25 USD
P 2022-02-01 AAPL 26.5 USD
"""

    file_path = tmp_path.joinpath("data.journal")
    file_path.touch()
    file_path.write_text(prices)
    file_tup = (str(file_path),)
    txns = lots_data.expected_qtty_reaches_zero_sell_all

    info = lots_info.LotInfo(file_tup, "AAPL", txns)
    return info


class TestLotInfo:
    @pytest.mark.parametrize("journal,expected", price_tests)
    def test_last_price(self, tmp_path: Path, journal: str, expected: float):
        txns = lots_data.expected_qtty_reaches_zero_sell_all
        file_path = tmp_path.joinpath("data.journal")
        file_path.touch()
        file_path.write_text(journal)
        file_tup = (str(file_path),)

        lot_info = lots_info.LotInfo(file_tup, "AAPL", txns)
        assert lot_info.get_last_price() == (date(2022, 2, 1), expected)

    def test_lots_xirr(self, basic_lot_info: LotInfo):
        assert basic_lot_info.xirr == pytest.approx(0.4613, abs=0.0001)

    def test_get_lots_info(self, basic_lot_info: LotInfo):
        expected = {
            "comm": "AAPL",
            "cur": "USD",
            "qtty": "5.0",
            "amount": "130.00",
            "avg_cost": "26.0000",
            "mkt_price": "26.5000",
            "mkt_amount": "132.50",
            "mkt_profit": "2.50",
            "mkt_date": "2022-02-01",
            "xirr": "46.1308%",
        }

        assert basic_lot_info.info == expected
