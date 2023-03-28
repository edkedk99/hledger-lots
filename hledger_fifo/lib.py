import os
from dataclasses import dataclass
from datetime import date
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
    if total_qtty == 0:
        return 0
    mult = [txn.qtty * txn.price for txn in txns]
    total_mult = sum(mult)
    avg = total_mult / total_qtty
    return avg


def get_default_file() -> Tuple[str, ...]:
    file_env = os.getenv("LEDGER_FILE")
    if file_env:
        return (file_env,)
    elif default_path.exists():
        return (str(default_path),)
    else:
        raise click.BadOptionUsage("file", "File missing")


def get_file_path(
    ctx: click.Context, _param, value: Optional[Tuple[str, ...]]
) -> Optional[Tuple[str, ...]]:  # type: ignore
    if value:
        return value

    if not ctx.parent:
        return None

    filenames: Optional[Tuple] = ctx.parent.params.get("file")
    if not filenames:
        raise click.BadOptionUsage("file", "File missing")

    return filenames


def get_files_comm(file_path: Tuple[str, ...]) -> List[str]:
    files = []
    for file in file_path:
        files = [*files, "-f", file]
    return files


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
