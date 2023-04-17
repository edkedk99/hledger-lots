# Automatic Market Prices Download

*Hledger-lots* can download daily market prices from [Yahoo Finance](https://finance.yahoo.com/) and append [market price directive](https://hledger.org/1.29/hledger.html#p-directive) to the journal, so you get updated *xirr* calculation and run regular hledger reports using market prices.

## Setup

Rename those commodities you want *hledger-lots* to download market according to the rule: **"y.[yahoo ticker name]"**. 

> **IMPORTANT:** You need to add double quotes between the commodity name because hledger accepts only word characters without it

Examples:

| Company   | Commodity name |
|-----------|----------------|
| Microsoft | "y.MSFT"       |
| Apple     | "y.AAPL"       |
| EUR/USD   | "y.EURUSD=X"   |
| Bitcoin   | "y.BTC-USD"    |

## Downloading

Run `hledger-lots list` or `hledger-lots-view` with the option flag `--append-prices-to [journal path]` or with environment variable **HLEDGER_APPEND_PRICES_TO**. The *journal path* can be either the journal file you are reading or another one you prefer to have your prices directives.

With the option above, *hledger-lots* will download the daily market prices for all the commodities that follows the commodity name rule. The time range follows the rule:

- If there is no market price for a commodity, it will download daily prices from the date of the first purchase until yesterday.
- If there is a market price for a commodity, it will download daily prices from the date following the last price directive to yesterday
