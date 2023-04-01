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


def check_available(txns: List[AdjustedTxn], account: str, sell_qtty: float):
    sum_qtty = sum(txn.qtty for txn in txns if txn.acct == account)
    if sell_qtty > sum_qtty:
        raise ValueError(
            f"You can't sell {sell_qtty:,.2f} in {account} because there is only {sum_qtty:,.2f} available"
        )
