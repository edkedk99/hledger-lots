import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from . import checks
from .lib import AdjustedTxn, get_xirr


@dataclass
class AvgCost:
    date: str
    total_qtty: float = 0
    total_amount: float = 0
    avg_cost: float = 0


def get_avg_cost(
    txns: List[AdjustedTxn], until: Optional[date] = None
) -> List[AvgCost]:
    if until:
        included_txns = [
            txn
            for txn in txns
            if datetime.strptime(txn.date, "%Y-%m-%d").date() <= until
        ]
    else:
        included_txns = txns

    checks.check_base_currency(included_txns)

    total_qtty = 0
    total_amount = 0
    avg_cost = 0

    avg_costs: List[AvgCost] = []

    for txn in included_txns:
        total_qtty += txn.qtty

        if txn.qtty >= 0:
            total_amount += txn.qtty * txn.price
        else:
            total_amount += txn.qtty * avg_cost

        avg_cost = total_amount / total_qtty if total_qtty != 0 else 0
        avg_costs.append(AvgCost(txn.date, total_qtty, total_amount, avg_cost))

    return avg_costs


def avg_sell(
    txns: List[AdjustedTxn],
    date: str,
    qtty: float,
    cur: str,
    cash_account: str,
    revenue_account: str,
    comm_account: str,
    value: float,
):
    checks.check_short_sell_current(txns, qtty)
    checks.check_base_currency(txns)
    checks.check_available(txns, comm_account, qtty)

    sell_date = datetime.strptime(date, "%Y-%m-%d").date()
    avg_cost = get_avg_cost(txns, sell_date)
    cost = avg_cost[-1].avg_cost
    last_avg_cost = avg_cost[-1]

    base_curr = txns[0].base_cur
    price = value / qtty
    xirr = get_xirr(price, sell_date, txns) or 0 * 100

    txn_hl = f"""{date} Sold {cur}
    ; commodity:{cur}, qtty:{qtty:,.2f}, price:{price:,.2f}
    ; xirr:{xirr:.2f}% annual percent rate 30/360US
    {cash_account}    {value:.2f} {base_curr}
    {comm_account}    {qtty * -1} {cur} @ {cost} {base_curr}
    {revenue_account}"""

    comm = ["hledger", "-f-", "print", "--explicit"]
    txn_proc = subprocess.run(comm, input=txn_hl.encode(), capture_output=True)

    txn_print: str = txn_proc.stdout.decode("utf8")
    return txn_print
