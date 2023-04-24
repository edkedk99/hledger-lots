import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import questionary
from prompt_toolkit.shortcuts import CompleteStyle

from . import avg, fifo
from .avg_info import AllAvgInfo
from .fifo_info import AllFifoInfo
from .files import get_files_comm
from .hl import hledger2txn


class PromptError(BaseException):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


@dataclass
class SellInfo:
    date: str
    quantity: float
    commodity: str
    cash_account: str
    revenue_account: str
    commodity_account: str
    price: float
    value: float


def get_append_file(default_file: str):
    confirm = questionary.confirm(
        "Add sale transaction to a journal", default=False, auto_enter=True
    ).ask()

    if confirm:
        file_append: str = questionary.path(
            "File to append transaction", default=default_file
        ).ask()
        comm = ["hledger", "-f", file_append, "check"]
        subprocess.run(comm, check=True)
        return file_append


def custom_autocomplete(name: str, choices: List[str]):
    question = questionary.autocomplete(
        f"{name} (TAB to autocomplete)",
        choices=choices,
        ignore_case=True,
        match_middle=True,
        style=questionary.Style([("answer", "fg:#f71b07")]),
        complete_style=CompleteStyle.MULTI_COLUMN,
    )
    return question


def val_date(date: str):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return "Invalid date format"


def val_qtty(answer: str, available: float):
    try:
        answer_float = float(answer)
    except ValueError:
        return "Invalid number"

    if answer_float < 0:
        return "Quantity should be positive"

    if answer_float > available:
        return "Quantity should be less than available"

    return True


def val_price(answer: str):
    if answer == "":
        return True

    try:
        answer_float = float(answer)
    except ValueError:
        return "Invalid number"

    if answer_float < 0:
        return "Price should be positive"

    return True


def val_total(answer: str):
    try:
        answer_float = float(answer)
    except ValueError:
        return "Invalid number"

    if answer_float < 0:
        return "Amount should be positive"

    return True


class PromptSell:
    def __init__(
        self,
        file: Tuple[str, ...],
        avg_cost: bool,
        check: bool,
        no_desc: Optional[str] = None,
    ) -> None:
        self.file = file
        self.avg_cost = avg_cost
        self.check = check
        self.no_desc = no_desc

        self.files_comm = get_files_comm(file)

        print(self.initial_info)
        self.info = self.get_info()

    def get_commodities_text(self, commodities: List[str]):
        answer = questionary.select(
            "Commodity",
            choices=commodities,
            use_shortcuts=True,
        ).ask()
        return answer

    def get_info(self):
        if self.avg_cost:
            infos = AllAvgInfo(self.file, self.no_desc or "", self.check)
        else:
            infos = AllFifoInfo(self.file, self.no_desc or "", self.check)

        commodities = [info["comm"] for info in infos.infos if float(info["qtty"]) > 0]
        commodity_text = self.get_commodities_text(commodities)
        info = next(item for item in infos.infos if item["comm"] == commodity_text)
        return info

    def get_last_purchase(self):
        commodity = self.info["comm"]

        comm = ["hledger", *self.files_comm, "reg", f"cur:{commodity}", "amt:>0"]
        reg_proc = subprocess.run(comm, capture_output=True)
        reg_txt = reg_proc.stdout.decode("utf8")
        rows_list = [row for row in reg_txt.split("\n") if row != ""]
        last_date = rows_list[-1][0:10]
        return last_date

    def get_accounts_list(self, *query: str):
        command = ["hledger", *self.files_comm, *query]
        proc = subprocess.run(command, capture_output=True)
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf8")
            raise PromptError(stderr)

        proc_list = proc.stdout.decode("utf8").split("\n")
        proc_list = [row for row in proc_list if row != ""]
        return proc_list

    def get_append_file(self):
        default_file = self.file[0]

        confirm = questionary.confirm(
            "Add sale transaction to a journal", default=False, auto_enter=True
        ).ask()

        if confirm:
            file_append: str = questionary.path(
                "File to append transaction", default=default_file
            ).ask()
            comm = ["hledger", "-f", file_append, "check"]
            subprocess.run(comm, check=True)
            return file_append

    def ask_date(self):
        last_purchase = self.get_last_purchase()

        answer: str = questionary.text(
            f"Date YYYY-MM-DD",
            validate=val_date,
            instruction=f"(Last Purchase: {last_purchase})",
        ).ask()
        return answer

    def ask_qtty(self):
        available = float(self.info["qtty"])

        answer_str: str = questionary.text(
            f"Quantity (available {available})",
            validate=lambda answer: val_qtty(answer, available),
            instruction="",
        ).ask()
        return answer_str

    def ask_price(self):
        cost_str = self.info["avg_cost"].replace(",", ".")
        cost = float(cost_str)

        answer_str: str = questionary.text(
            f"Price (avg cost: {cost})",
            validate=val_price,
            instruction="Empty to input total amount",
        ).ask()
        return answer_str

    def ask_total(self, qtty: float):
        available = qtty * float(self.info["avg_cost"])
        available_str = f"{available:,.2f}"

        answer_str: str = questionary.text(
            f"Total (available {available_str})",
            validate=val_total,
            instruction="Amount received",
        ).ask()
        return answer_str

    def ask_cash_account(self):
        accts = self.get_accounts_list("accounts")

        answer: str = custom_autocomplete("Cash Account", accts).ask()
        return answer

    def ask_commodity_account(self):
        commodity = self.info["comm"]
        accts = self.get_accounts_list("accounts", "note:Buy", f"cur:{commodity}")

        answer: str = questionary.select(
            "Commodity Account",
            choices=accts,
            use_shortcuts=True,
        ).ask()
        return answer

    def ask_revenue_account(self):
        accts = self.get_accounts_list("accounts")
        answer: str = custom_autocomplete("Revenue Account", accts).ask()
        return answer

    @property
    def initial_info(self):
        cost_method_text = "Average Cost" if self.avg_cost else "Fifo"
        no_desc_text = self.no_desc or "None"
        check_text = "Checking" if self.check else "Not Checking"

        files = [f if f != "-" else "stdin" for f in self.file]
        files_text = " ".join(files)

        result = f"""
Files              : {files_text}
Cost Method        : {cost_method_text} - {check_text}
Remove description : {no_desc_text}
"""
        return result

    def prompt(self):
        commodity = self.info["comm"]
        sell_date = self.ask_date()
        qtty = float(self.ask_qtty())
        price_str = self.ask_price()

        if price_str == "":
            value_str = self.ask_total(qtty)
            value = float(value_str)
            price = value / qtty
        else:
            price = float(price_str)
            value = qtty * price

        cash_acct = self.ask_cash_account()

        if self.avg_cost:
            commodity_acct = self.ask_commodity_account()
        else:
            commodity_acct = ""

        revenue_acct = self.ask_revenue_account()

        result = SellInfo(
            date=sell_date,
            quantity=qtty,
            commodity=commodity,
            cash_account=cash_acct,
            revenue_account=revenue_acct,
            commodity_account=commodity_acct,
            price=price,
            value=value,
        )

        return result

    def get_hl_txn(self):
        sell = self.prompt()
        commodity = sell.commodity
        adj_txns = hledger2txn(self.file, commodity, self.no_desc)

        if self.avg_cost:
            txn_print = avg.avg_sell(
                txns=adj_txns,
                date=sell.date,
                qtty=sell.quantity,
                cur=sell.commodity,
                cash_account=sell.cash_account,
                revenue_account=sell.revenue_account,
                comm_account=sell.commodity_account,
                value=sell.value,
                check=self.check,
            )
        else:
            sell_fifo = fifo.get_sell_lots(
                lots=adj_txns,
                sell_date=sell.date,
                sell_qtty=sell.quantity,
                check=self.check,
            )
            txn_print = fifo.txn2hl(
                txns=sell_fifo,
                date=sell.date,
                cur=sell.commodity,
                cash_account=sell.cash_account,
                revenue_account=sell.revenue_account,
                value=sell.value,
            )

        return txn_print
