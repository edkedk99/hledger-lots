import os
from dataclasses import dataclass
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
