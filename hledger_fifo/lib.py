from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from pyxirr import DayCount, xirr


@dataclass
class AdjustedTxn:
    date: str
    price: float
    base_cur: str
    qtty: float
    acct: str


@dataclass
class Txn(AdjustedTxn):
    type: str


def get_avg_fifo(txns: List[AdjustedTxn]):
    total_qtty = sum(txn.qtty for txn in txns)
    if total_qtty == 0:
        return 0
    mult = [txn.qtty * txn.price for txn in txns]
    total_mult = sum(mult)
    avg = total_mult / total_qtty
    return avg


def get_xirr(
    sell_price: float, sell_date: date, txns: List[AdjustedTxn]
) -> Optional[float]:
    dates = [txn.date for txn in txns]
    buy_amts = [txn.price * txn.qtty for txn in txns]
    total_qtty = sum(txn.qtty for txn in txns)

    sell_date_txt = sell_date.strftime("%Y-%m-%d")
    dates = [*dates, sell_date_txt]
    amts = [*buy_amts, -total_qtty * sell_price]
    sell_xirr = xirr(dates, amts, day_count=DayCount.THIRTY_U_360)
    return sell_xirr
