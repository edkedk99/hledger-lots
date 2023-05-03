# Automatic Market Prices Download

*Hledger-lots* can download daily market prices from [Yahoo Finance](https://finance.yahoo.com/) and output as [market price directive](https://hledger.org/1.29/hledger.html#p-directive), so you get updated *xirr* calculation and run regular hledger reports using market prices.

## Setup

Add a **yahoo_ticker** [tag](https://hledger.org/1.29/hledger.html#tags) to the comment of a [commodity directive](https://hledger.org/1.29/hledger.html#commodity-directive) with the value of the ticker in [Yahoo Finance](https://finance.yahoo.com/).

> **IMPORTANT:** You may need to add double quotes between the commodity name because hledger accepts only word characters without it

### Examples:

```text
commodity AAPL       ; yahoo_ticker:AAPL                                      
commodity "PETR4"    ; yahoo_ticker:PETR4.SA                                  
commodity BTC        ; yahoo_ticker:BTC-USD 
commodity EURUSD     ; yahoo_ticker:EURUSD=X
```

For output example, see [here](/hledger-lots/output/#prices)


## Downloading

Run `hledger-lots prices -f [journal file]`. For those commodities that have a *yahoo_ticker* tag according to the example above, *hledger-lots* will download daily historical prices in a date range according to the rule below, so the user doesn't need to care about start and end dates.

| Condition                             | Start Date                 | End Date    |
|---------------------------------------|----------------------------|-------------|
| no market price                       | First Purchase             | Yesterday   |
| have market price                     | Next day of the last price | Yesterday   |
| market price later or equal yesterday | No download                | No download |
