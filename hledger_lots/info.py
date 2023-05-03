import csv
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from typing import List, Optional, Tuple, TypedDict

from tabulate import tabulate

from .files import get_files_comm
from .hl import hledger2txn
from .lib import adjust_commodity, get_xirr


class LotsInfo(TypedDict):
    comm: str
    cur: str
    qtty: str
    amount: str
    avg_cost: str
    mkt_price: Optional[str]
    mkt_amount: Optional[str]
    mkt_profit: Optional[str]
    mkt_date: Optional[str]
    xirr: Optional[str]


@dataclass
class Price:
    date: date
    comm: str
    price: float
    cur: str


def get_last_price(files_comm: List[str], commodity: str):
    prices_comm = [
        "hledger",
        *files_comm,
        "prices",
        f"cur:{commodity}",
        "--infer-reverse-prices",
    ]
    prices_proc = subprocess.run(prices_comm, capture_output=True)
    prices_str = prices_proc.stdout.decode("utf8")

    if prices_str == "":
        return (None, None)

    prices_list = [row.split(" ", 3) for row in prices_str.split("\n") if row != ""]

    date_list = [
        (row[1], re.sub(r"[^0-9.]", "", row[3])) for row in prices_list if len(row) > 0
    ]

    if len(date_list) == 0:
        return (None, None)

    last_date_str = date_list[-1][0]
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    last_price = float(date_list[-1][1])
    return (last_date, last_price)


def get_commodities(journals: Tuple[str, ...]):
    files_comm = get_files_comm(journals)
    comm = ["hledger", *files_comm, "commodities"]
    commodities_proc = subprocess.run(comm, capture_output=True)
    commodities_str = commodities_proc.stdout.decode("utf8")

    commodities_list = [com for com in commodities_str.split("\n") if com != ""]
    return commodities_list


class Info:
    def __init__(
        self, journals: Tuple[str, ...], commodity: str, no_desc: Optional[str] = None
    ) -> None:
        self.journals = journals
        self.files_comm = get_files_comm(journals)
        self.commodity = commodity
        self.txns = hledger2txn(journals, commodity, no_desc)

        self.has_txn = len(self.txns) > 0
        self.last_price = get_last_price(self.files_comm, commodity)

        self.market_date, self.market_price = self.last_price

    def get_lots_xirr(self, last_buy_date: date):
        if self.market_date and self.market_price and self.market_date >= last_buy_date:
            xirr = get_xirr(self.market_price, self.market_date, self.txns)
            return xirr

    def get_info_txt(self, info: LotsInfo):
        info_txt = f"""
Info
----
Commodity:      {info['comm']}
Quantity:       {info['qtty']}
Amount:         {info['amount']}
Average Cost:   {info['avg_cost']}
"""

        if self.market_date or self.market_price:
            info_txt += f"""
Market Price:  {info['mkt_price']}
Market Amount: {info['mkt_amount']}
Market Profit: {info['mkt_profit']}
Market Date:   {info['mkt_date']}
Xirr:          {info['xirr']} (APR 30/360US)
"""
        else:
            info_txt += "\nMarket Data not available"

        return info_txt


class AllInfo:
    def __init__(self, journals: Tuple[str, ...], no_desc: str) -> None:
        self.journals = journals
        self.no_desc = no_desc
        self.commodities = get_commodities(journals)

    def get_infos_table(self, infos: List[LotsInfo], output_format: str):
        infos_list = [info for info in infos]
        infos_sorted = sorted(
            infos_list, key=lambda info: info["xirr"] or "", reverse=True
        )
        table = tabulate(
            infos_sorted,
            headers="keys",
            numalign="decimal",
            floatfmt=",.4f",
            tablefmt=output_format,
        )
        return table

    def get_infos_csv(self, infos: List[LotsInfo]):
        infos_list = [info for info in infos]
        infos_sorted = sorted(
            infos_list, key=lambda info: info["xirr"] or "", reverse=True
        )

        fieldnames = infos_sorted[0].keys()
        infos_io = StringIO()
        writer = csv.DictWriter(infos_io, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(infos_sorted)
        infos_io.seek(0)
        return infos_io
