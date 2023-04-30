import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

import questionary

from . import prompt
from .info import LotsInfo


@dataclass
class BuyInfo(prompt.Tradeinfo):
    base_cur: str


def val_buy_qtty(answer: str):
    try:
        answer_float = float(answer)
    except ValueError:
        return "Invalid number"

    if answer_float <= 0:
        return "Quantity should be positive"

    return True


class PromptBuy(prompt.Prompt):
    def __init__(
        self,
        file: Tuple[str, ...],
        avg_cost: bool,
        check: bool,
        no_desc: Optional[str] = None,
    ) -> None:
        super().__init__(file, avg_cost, check, no_desc)
        all_commodities_txt = self.run_hledger_no_query_desc("commodities")
        self.all_commodities = [
            com for com in all_commodities_txt.split("\n") if com != ""
        ]

        print(
            """
            Append a new purchase of a commodity.
            Use format format "y.ticker" to automatically download prices.
            Search on yahoo finance website the ticker for the commodity.\n"""
        )
        print(self.initial_info)
        self.info = self.get_info()
        self.last_purchase = self.get_last_purchase(self.info)

    def get_info(self):
        commodity = prompt.ask_commodities_text(self.all_commodities)
        info_not_found = LotsInfo(
            comm=commodity,
            cur="",
            qtty="0",
            amount="0",
            avg_cost="0",
            mkt_price=None,
            mkt_date=None,
            mkt_amount=None,
            mkt_profit=None,
            xirr=None,
        )
        info = next(
            (info for info in self.infos if info["comm"] == commodity), info_not_found
        )
        return info

    def ask_base_cur_text(self):
        if self.info["cur"] == "":
            answer: str = prompt.custom_autocomplete(
                "Base Currency", self.all_commodities
            ).ask()
        else:
            answer = self.info["cur"]
        return answer

    def ask_buy_qtty(self, info: LotsInfo):
        available = float(info["qtty"])

        answer_str: str = questionary.text(
            f"Quantity (available {available})",
            validate=val_buy_qtty,
            instruction="",
        ).ask()
        return answer_str

    def ask_commodity_account(self):
        accts_txt = self.run_hledger("accounts")
        accts = [acct for acct in accts_txt.split("\n") if acct != ""]
        answer: str = prompt.custom_autocomplete("Commodity Account", accts).ask()
        return answer

    def prompt(self):
        commodity = self.info["comm"]
        base_cur = self.ask_base_cur_text()
        sell_date = self.ask_date(self.last_purchase)
        qtty = float(self.ask_buy_qtty(self.info))
        price_str = self.ask_price(self.info)

        if price_str == "":
            value_str = self.ask_total(qtty, self.info)
            value = float(value_str)
            price = value / qtty
        else:
            price = float(price_str)
            value = qtty * price

        cash_acct = self.ask_cash_account()

        commodity_acct = self.ask_commodity_account()

        result = BuyInfo(
            date=sell_date,
            quantity=qtty,
            commodity=commodity,
            base_cur=base_cur,
            cash_account=cash_acct,
            commodity_account=commodity_acct,
            price=price,
            value=value,
        )
        return result

    def get_hl_txn(self):
        buy = self.prompt()

        txn_raw = f"""
{buy.date} Buy {buy.commodity}
    {buy.commodity_account}    {buy.quantity} \"{buy.commodity}\" @ {buy.price} \"{buy.base_cur}\"
    {buy.cash_account}
"""

        comm = ["hledger", "-f-", "print", "--explicit"]
        txn_proc = subprocess.run(
            comm,
            input=txn_raw.encode(),
            capture_output=True,
        )
        if txn_proc.returncode != 0:
            err = txn_proc.stderr.decode("utf8")
            raise prompt.PromptError(err)

        txn_print: str = txn_proc.stdout.decode("utf8")
        return txn_print
