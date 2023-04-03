import json
import subprocess
import sys
from typing import List, Optional, Tuple

from .files import get_files_comm
from .lib import AdjustedTxn, Txn, get_avg_fifo, get_xirr


def adjust_txn(txn: Txn) -> AdjustedTxn:
    price = txn.price if txn.type == "UnitPrice" else txn.price / txn.qtty

    result = AdjustedTxn(txn.date, price, txn.base_cur, txn.qtty, txn.acct)
    return result


def prices_items2txn(date: str, prices_items: dict, account: str) -> Txn:
    price = prices_items["aprice"]["contents"]["aquantity"]["floatingPoint"]
    base_cur = prices_items["aprice"]["contents"]["acommodity"]
    qtty = prices_items["aquantity"]["floatingPoint"]
    price_type = prices_items["aprice"]["tag"]

    txn = Txn(date, price, base_cur, qtty, account, price_type)
    return txn


def hledger2txn(
    file_path: Tuple[str, ...], cur: str, no_desc: Optional[str] = None
) -> List[AdjustedTxn]:
    files_comm = get_files_comm(file_path)
    comm = ["hledger", *files_comm, "print", f"cur:{cur}", "--output-format=json"]
    if no_desc:
        comm.append(f"not:desc:{no_desc}")

    hl_proc = subprocess.run(comm, stdin=sys.stdin, capture_output=True)
    if hl_proc.returncode != 0:
        raise ValueError(hl_proc.stderr.decode("utf8"))

    hl_data = hl_proc.stdout.decode("utf8")
    txns_list = json.loads(hl_data)

    txns = [
        prices_items2txn(txn["tdate"], prices_items, posting_items["paccount"])
        for txn in txns_list
        for posting_items in txn["tpostings"]
        for prices_items in posting_items["pamount"]
        if prices_items["acommodity"] == cur and prices_items["aprice"]
    ]

    adjusted_txns = [adjust_txn(txn) for txn in txns]
    return adjusted_txns
