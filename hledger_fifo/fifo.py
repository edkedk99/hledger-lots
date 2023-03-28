import copy
from typing import List

from .lib import AdjustedTxn


class MultipleBaseCurrencies(Exception):
    def __init__(self, currencies: set) -> None:
        self.currencies = currencies
        self.message = f"More than one base currency: {currencies}"


def check_short_sell_past(previous_buys: List[AdjustedTxn], sell: AdjustedTxn):
    previous_buys_qtty = sum([txn.qtty for txn in previous_buys])
    if abs(sell.qtty) > abs(previous_buys_qtty):
        raise ValueError(f"Short sell not allowed for sell {sell}")


def check_short_sell_current(previous_buys: List[AdjustedTxn], sell_qtty: float):
    previous_buys_qtty = sum([txn.qtty for txn in previous_buys])
    if sell_qtty > previous_buys_qtty:
        raise ValueError(
            f"Short sell not allowed for sell. You have {previous_buys_qtty:.4f}, which is less than you want to sell: {sell_qtty:.4f}"
        )


def check_base_currency(txns: List[AdjustedTxn]):
    base_currencies = set(txn.base_cur for txn in txns)
    if len(base_currencies) > 1:
        raise MultipleBaseCurrencies(base_currencies)


def get_lots(txns: List[AdjustedTxn]) -> List[AdjustedTxn]:
    local_txns = copy.deepcopy(txns)
    check_base_currency(txns)

    buys = [txn for txn in local_txns if txn.qtty >= 0]
    sells = [txn for txn in local_txns if txn.qtty < 0]

    buys_lot: List[AdjustedTxn] = buys if len(sells) == 0 else []
    for sell in sells:
        previous_buys = [txn for txn in buys if txn.date <= sell.date]
        check_short_sell_past(previous_buys, sell)
        later_buys = [txn for txn in buys if txn.date > sell.date]
        sell_qtty = abs(sell.qtty)

        i = 0
        while i < len(previous_buys) and sell_qtty > 0:
            previous_buy = previous_buys[i]
            if sell_qtty >= previous_buy.qtty:
                sell_qtty -= previous_buy.qtty
                previous_buys[i].qtty = 0
            else:
                previous_buys[i].qtty -= sell_qtty
                sell_qtty = 0
            i += 1

        buys_lot = [*previous_buys, *later_buys]

    return buys_lot


def get_sell_lots(lots: List[AdjustedTxn], sell_date: str, sell_qtty: float):
    check_short_sell_current(lots, sell_qtty)
    buy_lots = get_lots(lots)
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
