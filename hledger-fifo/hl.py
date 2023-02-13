import json
import subprocess
from io import TextIOWrapper
from typing import List

from .lib import AdjustedTxn, Txn, get_avg


def txn2hl(
    txns: List[AdjustedTxn],
    date: str,
    cur: str,
    cash_account: str,
    revenue_account: str,
    base_curr: str,
    value: float,
):
    avg_cost = get_avg(txns)
    sum_qtty = sum(txn.qtty for txn in txns)
    price = value / sum_qtty

    txn_hl = f"""
{date} Sold {cur}
    ; commodity:{cur}, qtty:{sum_qtty:,.2f}, price:{price:,.2f}, avg_fifo_cost:{avg_cost:,.4f}
    {cash_account}  {value:.2f} {base_curr}
"""

    for txn in txns:
        txn_hl += f"    {txn.acct}    {txn.qtty * -1} {cur} @ {txn.price} {base_curr}  ; buy_date:{txn.date}, base_cur:{txn.base_cur}\n"

    txn_hl += f"    {revenue_account}   "
    comm = ["hledger", "-f-", "print", "--explicit"]
    txn_proc = subprocess.run(comm, input=txn_hl.encode(), capture_output=True)
    txn_print: str = txn_proc.stdout.decode("utf8")
    return txn_print


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


def hledger2txn(data: TextIOWrapper, cur: str) -> List[AdjustedTxn]:
    comm = ["hledger", "-f-", "print", f"cur:{cur}", "--output-format=json"]
    hl_proc = subprocess.run(comm, stdin=data, capture_output=True)
    hl_data = hl_proc.stdout.decode("utf8")
    txns_list = json.loads(hl_data)

    txns = [
        prices_items2txn(txn["tdate"], prices_items, posting_items["paccount"])
        for txn in txns_list
        for posting_items in txn["tpostings"]
        for prices_items in posting_items["pamount"]
        if prices_items["acommodity"] == "AAPL"
    ]

    adjusted_txns = [adjust_txn(txn) for txn in txns]
    return adjusted_txns
