import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import yfinance as yf
from requests.exceptions import HTTPError
from requests_cache import CachedSession

from .commodity_tag import CommodityDirective, CommodityTag
from .files import get_files_comm
from .hl import hledger2txn
from .info import get_last_price


@dataclass
class Price:
    name: str
    date: date
    price: float
    cur: str


class YahooPrices:
    TAG = "yahoo_ticker"

    def __init__(self, files: Tuple[str, ...]) -> None:
        self.files = files
        self.files_comm = get_files_comm(files)

        self.session_path = Path.home() / "yfinance.cache"
        self.session = CachedSession(str(self.session_path))
        self.today = datetime.today()
        yesterday = self.today - timedelta(days=1)
        self.yesterday_str = yesterday.strftime("%Y-%m-%d")

        commodity_directive = CommodityDirective(self.files)
        self.commodities = commodity_directive.get_commodity_tag(self.TAG)

    def get_start_date(self, commodity: CommodityTag):
        txns = hledger2txn(self.files, commodity["commodity"])
        first_date_str = txns[0].date
        first_date = datetime.strptime(first_date_str, "%Y-%m-%d").date()
        last_market_date = get_last_price(self.files_comm, commodity["commodity"])[0]

        if not last_market_date:
            last_date = first_date
        elif last_market_date < first_date:
            last_date = first_date
        else:
            last_date = last_market_date

        start_date = last_date + timedelta(days=1)
        past = date.today() - start_date
        if past.days < 1:
            return

        return start_date

    def prices2hledger(self, prices: List[Price]):
        prices_list = [
            f"P {price.date.strftime('%Y-%m-%d')} \"{price.name}\" {price.price} {price.cur}"
            for price in prices
            if price
        ]
        prices_str = "\n".join(prices_list)
        return prices_str

    def get_prices(
        self,
        commodity: CommodityTag,
        start_date: str,
    ) -> List[Price]:
        ticker = yf.Ticker(commodity["value"], session=self.session)

        try:
            info: Dict[str, str] = ticker.info
        except HTTPError:
            print(f"; stderr: Can't download commodity {commodity}", file=sys.stderr)
            return []

        if not start_date:
            return []

        df = ticker.history(start=start_date, end=self.yesterday_str, raise_errors=True)

        prices = [
            Price(
                commodity["commodity"],
                row[0].to_pydatetime().date(),  # type:ignore
                row[1]["Close"],  # type: ignore
                info["currency"],
            )
            for row in df.iterrows()
        ]
        return prices

    def get_commodity_prices(self, commodity: CommodityTag):
        start_date = self.get_start_date(commodity)
        if not start_date:
            print(f"; stderr: No new data for {commodity}", file=sys.stderr)
            return

        start_date_str = start_date.strftime("%Y-%m-%d")
        try:
            prices = [
                price for price in self.get_prices(commodity, start_date_str) if price
            ]
            return prices
        except HTTPError:
            print(f"; stderr: {commodity['value']} not found", file=sys.stderr)
        except Exception:
            print(
                f"; stderr: Nothing downloaded for {commodity['value']} between {start_date} and {self.yesterday_str}",
                file=sys.stderr,
            )

    def print_prices(self):
        if len(self.commodities) == 0:
            print(
                f"\n\n; stderr: No commodities directives with tag {self.TAG}",
                file=sys.stderr,
            )
            return

        for commodity in self.commodities:
            prices = self.get_commodity_prices(commodity)
            if prices:
                print("\n")
                hledger_prices = self.prices2hledger(prices)
                print(hledger_prices)
