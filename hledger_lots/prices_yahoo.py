import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import yfinance as yf
from requests.exceptions import HTTPError
from requests_cache import CachedSession

from .files import get_files_comm
from .hl import hledger2txn
from .info import get_commodities, get_last_price


@dataclass
class Price:
    name: str
    date: date
    price: float
    cur: str


def get_start_date(txn_first_date: date, last_market_date: Optional[date]):
    if not last_market_date:
        last_date = txn_first_date
    elif last_market_date < txn_first_date:
        last_date = txn_first_date
    else:
        last_date = last_market_date

    start_date = last_date + timedelta(days=1)
    start_date_str = start_date.strftime("%Y-%m-%d")
    return start_date_str


def filter_yahoo(com: List[str]):
    y_match = (re.search(r"^(y\.)(.*)", item) for item in com)
    y_match = (item for item in y_match if item)
    y_match = [match.groups()[1] for match in y_match]
    return y_match


def prices2hledger(prices: List[Price]):
    prices_list = [
        f"P {price.date.strftime('%Y-%m-%d')} \"y.{price.name}\" {price.price} {price.cur}"
        for price in prices
        if price
    ]
    prices_str = "\n".join(prices_list)
    return prices_str


def get_yahoo_prices(
    ticker_name: str,
    start_date: str,
    end_date: str,
    session: CachedSession,
):
    ticker = yf.Ticker(ticker_name, session=session)
    info = ticker.info

    if start_date:
        df = ticker.history(start=start_date, end=end_date, raise_errors=True)
    else:
        df = ticker.history(period="1d", raise_errors=True)

    prices = [
        Price(
            ticker_name,
            row[0].to_pydatetime().date(),  # type:ignore
            row[1]["Close"],  # type: ignore
            info["currency"],
        )
        for row in df.iterrows()
    ]
    return prices


def get_hledger_prices(files: Tuple[str, ...], append_prices_to: Path):
    files_comm = get_files_comm(files)
    commodities = get_commodities(files)
    tickers = filter_yahoo(commodities)
    tickers_str = " ".join(tickers)
    print(
        f"stderr: Downloading price history for tickers: {tickers_str}", file=sys.stderr
    )

    session_path = Path.home() / "yfinance.cache"
    session = CachedSession(str(session_path))
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    with open(append_prices_to, "a") as f:
        f.write("\n")
        for ticker in tickers:
            commodity = f"y.{ticker}"
            txns = hledger2txn(files, commodity)
            txn_first_date_str = txns[0].date
            txn_first_date = datetime.strptime(txn_first_date_str, "%Y-%m-%d").date()

            last_market_date = get_last_price(files_comm, commodity)[0]
            start_date = get_start_date(txn_first_date, last_market_date)
            days_past = today.date() - datetime.strptime(start_date, "%Y-%m-%d").date()

            if days_past.days > 0:
                try:
                    prices = get_yahoo_prices(
                        ticker, start_date, yesterday_str, session
                    )
                    prices_hledger = prices2hledger(prices)
                    f.write(prices_hledger + "\n")
                except HTTPError:
                    print(f"stderr: {ticker} not found", file=sys.stderr)
                except Exception:
                    print(
                        f"stderr: Nothing downloaded for {ticker} between {start_date} and {yesterday_str}",
                        file=sys.stderr,
                    )

        f.write("\n")
