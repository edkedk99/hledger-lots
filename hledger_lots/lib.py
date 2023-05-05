import os
import re
import shlex
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

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


def get_file_from_stdin():
    tmp_file = tempfile.NamedTemporaryFile(suffix=".journal", delete=False)
    name = tmp_file.name

    with open(tmp_file.name, "w") as f:
        for line in sys.stdin:
            f.write(line)

    return name


def get_default_file():
    ledger_file = os.getenv("LEDGER_FILE")
    if ledger_file:
        return (ledger_file,)

    default_path = Path.home() / ".hledger.journal"
    if default_path.exists():
        return (str(default_path),)


def get_files_comm(file_path: Tuple[str, ...]) -> List[str]:
    files = []
    for file in file_path:
        files = [*files, "-f", file]
    return files


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


def adjust_commodity(comm: str):
    has_non_word = re.search(r"\W", comm)
    adjusted = f'"{comm}"' if has_non_word else comm
    return adjusted


def get_sell_comm(
    commodity: str,
    no_desc: str,
    commodity_account: str,
    cash_account: str,
    revenue_account: str,
    date: str,
    quantity: float,
    price: float,
    avg_cost: bool,
):
    avg_comm = ["-g"] if avg_cost else []
    no_desc_comm = ["n", no_desc] if no_desc else []

    comm = [
        "hledger-lots",
        "sell",
        *avg_comm,
        *no_desc_comm,
        "-c",
        commodity,
        "-s",
        commodity_account,
        "-a",
        cash_account,
        "-r",
        revenue_account,
        "-d",
        date,
        "-q",
        str(quantity),
        "-p",
        str(price),
    ]
    comm_str: str = shlex.join(comm)

    return comm_str
