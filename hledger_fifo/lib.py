import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import click
from pyxirr import DayCount, xirr

ENV_FILE = "LEDGER_FILE"
default_path = Path.home() / ".hledger.journal"


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


def get_avg(txns: List[AdjustedTxn]):
    total_qtty = sum(txn.qtty for txn in txns)
    mult = [txn.qtty * txn.price for txn in txns]
    total_mult = sum(mult)
    avg = total_mult / total_qtty
    return avg


def get_default_file() -> Optional[Tuple[str]]:
    file_env = os.getenv("LEDGER_FILE")
    if file_env:
        return tuple(file_env)

    if default_path.exists():
        return tuple(str(default_path))


def get_file_path(
    ctx: click.Context, _param: click.Parameter, value: Tuple[str, ...]
) -> Optional[Tuple[str, ...]]:
    if value:
        return value

    if not ctx.parent:
        raise click.BadOptionUsage("file", "File missing")

    filenames: Optional[Tuple] = ctx.parent.params.get("file")
    if not filenames:
        raise click.BadOptionUsage("file", "File missing")

    return filenames


def get_xirr(sell_price: float, sell_date: str, txns: List[AdjustedTxn]) -> float:
    dates = [txn.date for txn in txns]
    buy_amts = [txn.price * txn.qtty for txn in txns]
    total_qtty = sum(txn.qtty for txn in txns)

    dates = [*dates, sell_date]
    amts = [*buy_amts, -total_qtty * sell_price]
    sell_xirr = xirr(dates, amts, day_count=DayCount.THIRTY_U_360)
    if sell_xirr:
        return sell_xirr
    else:
        return 0


def get_last_price(prices_file: str, base_cur: str):
    prices_comm = [
        "hledger",
        "-f",
        prices_file,
        "prices",
        f"cur:{base_cur}",
        "--infer-reverse-prices",
    ]
    prices_proc = subprocess.run(prices_comm, capture_output=True)
    prices_str = prices_proc.stdout.decode("utf8")

    if prices_str == "":
        return None

    prices_list = prices_str.split("\n")
    date_list = [
        (item[1], item[3]) for row in prices_list for item in row if base_cur in item[3]
    ]
    last_price = date_list[-1]
    return last_price


def get_lots_xirr(prices_file: str, base_cur: str, lots: List[AdjustedTxn]):
    last_price = get_last_price(prices_file, base_cur)
    if not last_price:
        return None

    sell_price = float(last_price[1])

    last_buy_date = datetime.strptime(lots[-1].date, "%Y-%m-%d")
    sell_date = datetime.strptime(last_price[0], "%Y-%m-%d")
    if (last_buy_date) > sell_date:
        return None

    xirr = get_xirr(sell_price, last_price[0], lots)
    if not xirr:
        return None

    return xirr
