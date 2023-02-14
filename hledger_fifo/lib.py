from dataclasses import dataclass
from typing import List


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
