import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import questionary
from prompt_toolkit.shortcuts import CompleteStyle

from .avg_info import AllAvgInfo
from .fifo_info import AllFifoInfo
from .files import get_files_comm
from .info import LotsInfo


class PromptError(BaseException):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


@dataclass
class Tradeinfo:
    date: str
    quantity: float
    commodity: str
    cash_account: str
    commodity_account: str
    price: float
    value: float


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


def select_commodities_text(commodities: List[str]):
    answer = questionary.select(
        "Commodity",
        choices=commodities,
        use_shortcuts=True,
    ).ask()
    return answer


def ask_commodities_text(commodities: List[str]):
    answer: str = custom_autocomplete("Commodity", commodities).ask()
    return answer


def val_date(date: str):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return "Invalid date format"


def val_sell_qtty(answer: str, available: float):
    try:
        answer_float = float(answer)
    except ValueError:
        return "Invalid number"

    if answer_float <= 0:
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


class Prompt:
    def __init__(
        self,
        file: Tuple[str, ...],
        avg_cost: bool,
        check: bool,
        no_desc: Optional[str] = None,
    ) -> None:
        self.file = file
        self.check = check
        self.no_desc = no_desc
        self.avg_cost = avg_cost

        self.files_comm = get_files_comm(file)
        self.infos = self.get_infos()
        self.commodities = [info["comm"] for info in self.get_infos()]

    def run_hledger(self, *comm: str):
        command = ["hledger", *self.files_comm, *comm, f"not:desc:{self.no_desc}"]
        proc = subprocess.run(command, capture_output=True)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(proc.stderr.decode("utf8"))

        result = proc.stdout.decode("utf8")
        return result

    def run_hledger_no_query_desc(self, *comm: str):
        command = ["hledger", *self.files_comm, *comm]
        proc = subprocess.run(command, capture_output=True)
        if proc.returncode != 0:
            raise subprocess.SubprocessError(proc.stderr.decode("utf8"))

        result = proc.stdout.decode("utf8")
        return result

    def get_infos(self):
        if self.avg_cost:
            infos = AllAvgInfo(self.file, self.no_desc or "", self.check)
        else:
            infos = AllFifoInfo(self.file, self.no_desc or "", self.check)

        valid_infos = [info for info in infos.infos if float(info["qtty"]) > 0]
        return valid_infos

    def get_last_purchase(self, info: LotsInfo):
        commodity = info["comm"]
        reg = self.run_hledger("reg", f"cur:{commodity}", "amt:>0")
        rows_list = [row for row in reg.split("\n") if row != ""]

        if len(rows_list) > 0:
            last_date = rows_list[-1][0:10]
            return last_date

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

    def ask_date(self, last_purchase: Optional[str]):
        last_purchase = last_purchase

        answer: str = questionary.text(
            f"Date YYYY-MM-DD",
            validate=val_date,
            instruction=f"(Last Purchase: {last_purchase})",
        ).ask()
        return answer

    def ask_sell_qtty(self, info: LotsInfo):
        available = float(info["qtty"])

        answer_str: str = questionary.text(
            f"Quantity (available {available})",
            validate=lambda answer: val_sell_qtty(answer, available),
            instruction="",
        ).ask()
        return answer_str

    def ask_price(self, info: LotsInfo):
        cost_str = info["avg_cost"].replace(",", ".")
        cost = float(cost_str)

        answer_str: str = questionary.text(
            f"Price (avg cost: {cost})",
            validate=val_price,
            instruction="Empty to input total amount",
        ).ask()
        return answer_str

    def ask_total(self, qtty: float, info: LotsInfo):
        available = qtty * float(info["avg_cost"])
        available_str = f"{available:,.2f}"

        answer_str: str = questionary.text(
            f"Total (available {available_str})",
            validate=val_total,
            instruction="Amount received",
        ).ask()
        return answer_str

    def ask_cash_account(self):
        accts_txt = self.run_hledger("accounts")
        accts = [acct for acct in accts_txt.split("\n") if acct != ""]
        answer: str = custom_autocomplete("Cash Account", accts).ask()
        return answer

    def ask_revenue_account(self):
        accts_txt = self.run_hledger("accounts")
        accts = [acct for acct in accts_txt.split("\n") if acct != ""]
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
