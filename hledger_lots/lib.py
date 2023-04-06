import os
from dataclasses import asdict, dataclass
from datetime import date
from typing import List, Optional

from pyxirr import DayCount, xirr
from tabulate import tabulate


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


class CostMethodError(Exception):
    def __init__(self, sell: AdjustedTxn, price: float, base_cur: str) -> None:
        self.message = f"Error in sale {sell}. Correct price should be {price} in currency {base_cur}"
        super().__init__(self.message)


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
    if len(txns) == 0:
        return 0

    dates = [txn.date for txn in txns]
    buy_amts = [txn.price * txn.qtty for txn in txns]
    total_qtty = sum(txn.qtty for txn in txns)

    sell_date_txt = sell_date.strftime("%Y-%m-%d")
    dates = [*dates, sell_date_txt]
    amts = [*buy_amts, -total_qtty * sell_price]
    sell_xirr = xirr(dates, amts, day_count=DayCount.THIRTY_U_360)
    return sell_xirr


def dt_list2table(dt_list: List, tablefmt: str = "simple"):
    lots_dict = [asdict(dt) for dt in dt_list]
    table = tabulate(
        lots_dict,
        headers="keys",
        numalign="decimal",
        floatfmt=",.4f",
        tablefmt=tablefmt,
    )
    return table


def default_fn_bool(env_name: str, default: bool):
    env = os.environ.get(env_name, None)
    if env == "true":
        return True
    elif env == "False":
        return False
    else:
        return default
