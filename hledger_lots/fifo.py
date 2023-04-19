import copy
import subprocess
from datetime import datetime
from typing import List

from . import checks
from .lib import AdjustedTxn, CostMethodError, adjust_commodity, get_avg_fifo, get_xirr


def check_sell(sell: AdjustedTxn, previous_buys: List[AdjustedTxn], check: bool):
    if not check:
        return

    diff_zero = [
        previous_buy for previous_buy in previous_buys if previous_buy.qtty != 0
    ]
    if len(diff_zero) == 0:
        return

    previous_buy = diff_zero[0]
    if sell.price != previous_buy.price or sell.base_cur != previous_buy.base_cur:
        raise CostMethodError(sell, previous_buy.price, previous_buy.base_cur)


def get_lots(txns: List[AdjustedTxn], check: bool) -> List[AdjustedTxn]:
    local_txns = copy.deepcopy(txns)
    checks.check_base_currency(txns)

    buys = [txn for txn in local_txns if txn.qtty >= 0]
    sells = [txn for txn in local_txns if txn.qtty < 0]

    buys_lot: List[AdjustedTxn] = buys if len(sells) == 0 else []
    for sell in sells:
        previous_buys = [txn for txn in buys if txn.date <= sell.date]
        checks.check_short_sell_past(previous_buys, sell)
        later_buys = [txn for txn in buys if txn.date > sell.date]
        sell_qtty = abs(sell.qtty)

        i = 0
        while i < len(previous_buys) and sell_qtty > 0:
            previous_buy = previous_buys[i]
            check_sell(sell, previous_buys, check)
            if sell_qtty >= previous_buy.qtty:
                sell_qtty -= previous_buy.qtty
                previous_buys[i].qtty = 0
            else:
                previous_buys[i].qtty -= sell_qtty
                sell_qtty = 0

            i += 1

        buys_lot = [*previous_buys, *later_buys]

    return buys_lot


def get_sell_lots(
    lots: List[AdjustedTxn], sell_date: str, sell_qtty: float, check: bool
):
    checks.check_short_sell_current(lots, sell_qtty)
    buy_lots = get_lots(lots, check)
    previous_buys = [lot for lot in buy_lots.copy() if lot.date <= sell_date]

    fifo_lots: List[AdjustedTxn] = []
    sell_qtty_curr = sell_qtty

    i = 0
    while sell_qtty_curr > 0 and i < len(lots):
        buy = previous_buys[i]
        if buy.qtty == 0:
            pass
        elif sell_qtty_curr > buy.qtty:
            fifo_lots.append(
                AdjustedTxn(buy.date, buy.price, buy.base_cur, buy.qtty, buy.acct)
            )
            sell_qtty_curr -= buy.qtty
        else:
            fifo_lots.append(
                AdjustedTxn(buy.date, buy.price, buy.base_cur, sell_qtty_curr, buy.acct)
            )
            sell_qtty_curr = 0
        i += 1

    return fifo_lots


def txn2hl(
    txns: List[AdjustedTxn],
    date: str,
    cur: str,
    cash_account: str,
    revenue_account: str,
    value: float,
):
    adj_comm = adjust_commodity(cur)
    base_curr = txns[0].base_cur
    avg_cost = get_avg_fifo(txns)
    sum_qtty = sum(txn.qtty for txn in txns)
    price = value / sum_qtty
    dt = datetime.strptime(date, "%Y-%m-%d").date()
    xirr = get_xirr(price, dt, txns) or 0 * 100

    txn_hl = f"""
{date} Sold {cur}  ; cost_method:fifo
    ; commodity:{cur}, qtty:{sum_qtty:,.2f}, price:{price:,.2f}
    ; avg_cost:{avg_cost:,.4f}, xirr:{xirr:.2f}% annual percent rate 30/360US
    {cash_account}  {value:.2f} {base_curr}
"""

    for txn in txns:
        txn_hl += f"    {txn.acct}    {txn.qtty * -1} {adj_comm} @ {txn.price} {base_curr}  ; buy_date:{txn.date}, base_cur:{txn.base_cur}\n"

    txn_hl += f"    {revenue_account}   "
    comm = ["hledger", "-f-", "print", "--explicit"]
    txn_proc = subprocess.run(
        comm,
        input=txn_hl.encode(),
        capture_output=True,
    )
    txn_print: str = txn_proc.stdout.decode("utf8")
    return txn_print
