# Output examples
## sell

Besides the transaction, constructed according to *FIFO* without any manual intervention, you have as tags the quantity and price sold, the average cost using *FIFO* and the *xirr* of the transaction, as explained [here](README.md#xirr) 

```txt
2023-04-01 Sold AAPL
    ; commodity:AAPL, qtty:6.00, price:6.50
    ; avg_fifo_cost:5.1167, xirr:1.62% annual percent rate 30/360US
    Asset:Bank                        39.00 USD
    Asset:Stocks            -5.0 AAPL @ 5.1 USD  ; buy_date:2023-01-01
    Asset:Stocks            -1.0 AAPL @ 5.2 USD  ; buy_date:2023-01-05
    Revenue:Capital Gain              -8.30 USD
```

## lots

```txt
date          price  base_cur      qtty  acct
----------  -------  ----------  ------  ------------
2022-01-05   4.0000  USD              0  Asset:Stocks
2022-01-10   5.0000  USD              0  Asset:Stocks
2022-01-20   5.8000  USD              0  Asset:Stocks
2022-02-15   5.1000  USD              0  Asset:Stocks
2023-01-01   5.1000  USD              5  Asset:Stocks
2023-01-05   5.2000  USD              3  Asset:Stocks

Info
----
Commodity:      AAPL
Quantity:       8
Amount:         41.10
Average Cost:   5.1375

Market Price:  6.2000
Market Amount: 49.60
Market Profit: 8.50
Market Date:   2023-07-01
Xirr:          46.1056% (APR 30/360US)
```

## Info

### plain

```txt
comm    cur      qtty    amount    avg_cost  mkt_price    mkt_amount    mkt_profit    mkt_date    xirr
AAPL    USD         8   41.1000      5.1375  6.2000       49.60         8.50          2023-07-01  46.1056%
BRL     USD        55   10.0000      0.1818
GOOG    USD         3   57.0000     19.0000
```

### pretty

```txt
┍━━━━━━━━┯━━━━━━━┯━━━━━━━━┯━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━┑
│ comm   │ cur   │   qtty │   amount │   avg_cost │ mkt_price   │ mkt_amount   │ mkt_profit   │ mkt_date   │ xirr     │
┝━━━━━━━━┿━━━━━━━┿━━━━━━━━┿━━━━━━━━━━┿━━━━━━━━━━━━┿━━━━━━━━━━━━━┿━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━┿━━━━━━━━━━━━┿━━━━━━━━━━┥
│ AAPL   │ USD   │      8 │  41.1000 │     5.1375 │ 6.2000      │ 49.60        │ 8.50         │ 2023-07-01 │ 46.1056% │
├────────┼───────┼────────┼──────────┼────────────┼─────────────┼──────────────┼──────────────┼────────────┼──────────┤
│ BRL    │ USD   │     55 │  10.0000 │     0.1818 │             │              │              │            │          │
├────────┼───────┼────────┼──────────┼────────────┼─────────────┼──────────────┼──────────────┼────────────┼──────────┤
│ GOOG   │ USD   │      3 │  57.0000 │    19.0000 │             │              │              │            │          │
┕━━━━━━━━┷━━━━━━━┷━━━━━━━━┷━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━┙
```

### csv

```txt
comm,cur,qtty,amount,avg_cost,mkt_price,mkt_amount,mkt_profit,mkt_date,xirr
AAPL,USD,8,41.10,5.1375,6.2000,49.60,8.50,2023-07-01,46.1056%
BRL,USD,55,10.00,0.1818,,,,,
GOOG,USD,3,57.00,19.0000,,,,,
```
