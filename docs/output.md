# Output examples
## sell

Besides the transaction, constructed according to *FIFO* or *AVERAGE COST* without any manual intervention, you have as tags the quantity and price sold, the average cost using *FIFO* and the *xirr* of the transaction, as explained [here](README.md#xirr) 

[![asciicast](https://asciinema.org/a/zzEMCtDAlqAlza1hMlxynKMWy.svg)](https://asciinema.org/a/zzEMCtDAlqAlza1hMlxynKMWy)

## prices

Prices directives are printed to stdout, while error logs are printed to stderr so you can append stdout to a file without the error logs

```text


P 2023-04-17 "AAPL" 165.22999572753906 USD
P 2023-04-18 "AAPL" 166.47000122070312 USD
P 2023-04-19 "AAPL" 167.6300048828125 USD
P 2023-04-20 "AAPL" 166.64999389648438 USD
P 2023-04-21 "AAPL" 165.02000427246094 USD
P 2023-04-24 "AAPL" 165.3300018310547 USD
P 2023-04-25 "AAPL" 163.77000427246094 USD
P 2023-04-26 "AAPL" 163.75999450683594 USD
P 2023-04-27 "AAPL" 168.41000366210938 USD
P 2023-04-28 "AAPL" 169.67999267578125 USD
P 2023-05-01 "AAPL" 169.58999633789062 USD
; stderr: Nothing downloaded for PETR4.SA between 2023-04-29 and 2023-05-02
```

## view

```bash
$ python -m hledger_lots -f docs/examples/data.journal  view -c AAPL
date          price  base_cur      qtty  acct
----------  -------  ----------  ------  ------------
2022-01-05      160  USD              0  Asset:Stocks
2022-01-10      145  USD              4  Asset:Stocks
2022-01-20      168  USD             15  Asset:Stocks

Info
----
Commodity:      AAPL
Quantity:       19
Amount:         3,100.00
Average Cost:   163.1579

Market Price:  163.7700
Market Amount: 3,111.63
Market Profit: 11.63
Market Date:   2023-04-25
Xirr:          0.0029% (APR 30/360US)

```

## list

### plain

```bash
$ python -m hledger_lots -f docs/examples/data.journal list
comm    cur      qtty  amount      avg_cost    mkt_price  mkt_amount      mkt_profit  mkt_date    xirr
GOOG  USD         3  306.00      102.0000     104.6100  313.83              7.8300  2023-04-25  0.0200%
AAPL  USD        19  3,100.00    163.1579     163.7700  3,111.63           11.6300  2023-04-25  0.0029%
```

### pretty

```bash
$ python -m hledger_lots -f docs/examples/data.journal list --output-format pretty
┍━━━━━━━━┯━━━━━━━┯━━━━━━━━┯━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━┑
│ comm   │ cur   │   qtty │ amount   │   avg_cost │   mkt_price │ mkt_amount   │   mkt_profit │ mkt_date   │ xirr    │
┝━━━━━━━━┿━━━━━━━┿━━━━━━━━┿━━━━━━━━━━┿━━━━━━━━━━━━┿━━━━━━━━━━━━━┿━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━┿━━━━━━━━━━━━┿━━━━━━━━━┥
│ GOOG   │ USD   │      3 │ 306.00   │   102.0000 │    104.6100 │ 313.83       │       7.8300 │ 2023-04-25 │ 0.0200% │
├────────┼───────┼────────┼──────────┼────────────┼─────────────┼──────────────┼──────────────┼────────────┼─────────┤
│ AAPL   │ USD   │     19 │ 3,100.00 │   163.1579 │    163.7700 │ 3,111.63     │      11.6300 │ 2023-04-25 │ 0.0029% │
┕━━━━━━━━┷━━━━━━━┷━━━━━━━━┷━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━┙
```

### csv

```bash
$ python -m hledger_lots -f docs/examples/data.journal list --output-format csv
comm,cur,qtty,amount,avg_cost,mkt_price,mkt_amount,mkt_profit,mkt_date,xirr
GOOG,USD,3,306.00,102.0000,104.6100,313.83,7.83,2023-04-25,0.0200%
AAPL,USD,19,"3,100.00",163.1579,163.7700,"3,111.63",11.63,2023-04-25,0.0029%
```

## --check/no-check

The error below was raised for a sale transaction generated using *AVERAGE COST* after trying to use the *view* command not setting "--avg-cost", so *FIFO* was used. This command raised a *CostMethodError* because the cost was not the one expected:

```bash
$ hledger_lots -f test.journal view -c AAPL --check

hledger_lots.lib.CostMethodError: Error in sale AdjustedTxn(date='2023-03-10', price=1.3066666667, base_cur='BRL', qtty=-15, acct='Ativo:Acoes:AAPL'). Correct price should be 1.2 in currency BRL*
```
