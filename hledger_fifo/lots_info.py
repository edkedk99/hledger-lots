import csv
import re
import subprocess
from datetime import datetime
from io import StringIO
from typing import List, Optional, Tuple, TypedDict

from tabulate import tabulate

from .fifo import MultipleBaseCurrencies, get_lots
from .hl import hledger2txn
from .lib import AdjustedTxn, get_avg, get_files_comm, get_xirr


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


class LotInfo:
    def __init__(
        self,
        journals: Tuple[str, ...],
        commodity: str,
        lots: List[AdjustedTxn],
    ) -> None:
        self.journals = journals
        self.files_comm = get_files_comm(journals)
        self.commodity = commodity

        self.lots = lots
        self.last_buy_date = datetime.strptime(lots[-1].date, "%Y-%m-%d").date()

        self.market_date, self.market_price = self.get_last_price()
        self.xirr = self.get_lots_xirr()

        self.info = self.get_lots_info()

    def get_last_price(self):
        prices_comm = [
            "hledger",
            *self.files_comm,
            "prices",
            f"cur:{self.commodity}",
            "--infer-reverse-prices",
        ]
        prices_proc = subprocess.run(prices_comm, capture_output=True)
        prices_str = prices_proc.stdout.decode("utf8")

        if prices_str == "":
            return (None, None)

        prices_list = [row.split(" ", 3) for row in prices_str.split("\n") if row != ""]

        date_list = [
            (row[1], re.sub(r"[a-zA-Z]|\,|\s", "", row[3]))
            for row in prices_list
            if row[2] == self.commodity
        ]

        if len(date_list) == 0:
            return (None, None)

        last_date_str = date_list[-1][0]
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        last_price = float(date_list[-1][1])
        return (last_date, last_price)

    def get_lots_xirr(self):
        if (
            self.market_date
            and self.market_price
            and self.market_date >= self.last_buy_date
        ):
            xirr = get_xirr(self.market_price, self.market_date, self.lots)
            return xirr

    def get_lots_info(self):
        commodity = self.commodity
        cur = self.lots[0].base_cur
        qtty = sum(lot.qtty for lot in self.lots)
        amount = sum(lot.price * lot.qtty for lot in self.lots)
        avg_cost = get_avg(self.lots) if qtty > 0 else 0

        if self.market_price and self.market_date and self.xirr:
            market_price_str = f"{self.market_price:,.4f}"
            market_amount = self.market_price * qtty
            market_amount_str = f"{market_amount:,.2f}"
            market_profit = market_amount - amount
            market_profit_str = f"{market_profit:,.2f}"
            market_date = self.market_date.strftime("%Y-%m-%d")
            xirr = self.xirr * 100
            xirr_str = f"{xirr:,.4f}%"
        else:
            market_amount_str = ""
            market_profit_str = ""
            market_date = ""
            market_price_str = ""
            xirr_str = ""

        return LotsInfo(
            comm=commodity,
            cur=cur,
            qtty=str(qtty),
            amount=f"{amount:,.2f}",
            avg_cost=f"{avg_cost:,.4f}",
            mkt_price=market_price_str,
            mkt_amount=market_amount_str,
            mkt_profit=market_profit_str,
            mkt_date=market_date,
            xirr=xirr_str,
        )

    @property
    def info_txt(self):
        info_txt = f"""
Info
----
Commodity:      {self.info['comm']}
Quantity:       {self.info['qtty']}
Amount:         {self.info['amount']}
Average Cost:   {self.info['avg_cost']}
"""

        if self.market_date or self.market_price:
            info_txt += f"""
Market Price:  {self.info['mkt_price']}
Market Amount: {self.info['mkt_amount']}
Market Profit: {self.info['mkt_profit']}
Market Date:   {self.info['mkt_date']}
Xirr:          {self.info['xirr']} (APR 30/360US)
"""
        else:
            info_txt += "\nMarket Data not available"

        return info_txt


class AllInfo:
    def __init__(self, journals: Tuple[str, ...], no_desc: str) -> None:
        self.journals = journals
        self.no_desc = no_desc

        self.commodities = self.get_commodities()
        self.infos = self.get_infos()

    def get_commodities(self):
        files_comm = get_files_comm(self.journals)
        comm = ["hledger", *files_comm, "commodities"]
        commodities_proc = subprocess.run(comm, capture_output=True)
        commodities_str = commodities_proc.stdout.decode("utf8")

        commodities_list = [com for com in commodities_str.split("\n")]
        return commodities_list

    def get_info(self, commodity: str):
        txns = hledger2txn(self.journals, commodity, self.no_desc)
        try:
            lots = get_lots(txns)
        except MultipleBaseCurrencies:
            return None

        if len(lots) > 0:
            lot_info = LotInfo(self.journals, commodity, lots)
            return lot_info

    def get_infos(self):
        infos = [self.get_info(com) for com in self.commodities]
        infos = [info for info in infos if info is not None]
        return infos

    def get_infos_table(self, output_format: str):
        infos_list = [info.info for info in self.infos]
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

    def get_infos_csv(self):
        infos_list = [info.info for info in self.infos]
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
