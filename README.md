# hledger-fifo

## Introduction

This script aims to help hledger's user to add transactions involving buying and selling commodities, which can be FOREX or investments assets, for example

When you sell a commodity, you should use the cost and quantity from the purchase date, which is buried deep down in your journal file so you have hledger accounting the correct _Capital Gain_ and use one accounting stock cost method.

This package uses **FIFO** method (First-In-First-Out-Method) to create a sale transaction according to information provided by the user and traverse the journal file to determine what quantity and lot prices should be used and generate a valid hledger transaction to be appended to the journal with additional helpful calculations as comment tags.

It also generate **FIFO** lots reports so the user can understand his situation with a commodity and check the correctness of the generated sell transaction.

## Requirements

- python
- hledger

## Instalation

```python
pip install --force-reinstall git+https://github.com/edkedk99/hledger-fifo.git
```

## Usage

Hledger-fifo offers two subcommands: **sell and lots**. The user should inform the journal filename or pipe the journal to the command and provide additional information using flags or insert when prompted interactively if any information is missing, something similar to _hledger_add_. See general command help below:

Download the example journal file to test this package.

```
Usage: hledger-fifo [OPTIONS] COMMAND [ARGS]...

  Commands to apply FIFO(first-in-first-out) accounting principles without
  manual management of lots. Useful for transactions involving purchase and
  selling foreign currencies or stocks.

Options:
  -h, --help  Show this message and exit.

Commands:
  lots  Report lots for a commodity.
  sell  Create a transaction with automatic FIFO for a commodity.
```

### sell

Run the command according to the subcommand help:

```
Usage: hledger-fifo sell [OPTIONS]

  Create a transaction with automatic FIFO for a commodity.

  Generate a transaction that represents a sale of a commodity with the
  following postings:

  - First posting: Positive amount on the 'base-currency' in the account that
  receives the product of the sale.

  - Multiple lot postings: Each posting is a different lot you are selling for
  the cost price on purchasing date, calculated according to FIFO accounting
  principles.

  - Revenue posting: posting that represent Capital Gain or Loss as the
  difference between the total cost and the amount received on the base-
  currency.

  This command also add transaction's comment with the following information
  as tags: commodity, total quantity sold, average FIFO cost and xirr

  All flags, except '--file' will be interactively prompted if absent, much
  like 'hledger-add'.

Options:
  -f, --file FILENAME         journal file. Without this flag or '-f-', will
                              read from stdin  [required]
  -c, --commodity TEXT        Commodity you are selling
  -b, --base-currency TEXT    Currency on which you are receiving for the sale
  -a, --cash-account TEXT     What account entered the product of the sell
  -r, --revenue-account TEXT  Account that represent capital gain/loss
  -d, --date TEXT             Date of the transaction (YYYY-mm-dd)
  -q, --quantity FLOAT
  -p, --price FLOAT
```

#### Output example

```
2023-04-01 Sold AAPL
    ; commodity:AAPL, qtty:6.00, price:6.50
    ; avg_fifo_cost:5.1167, xirr:162.33% annual percent rate 30/360US
    Asset:Bank                        39.00 USD
    Asset:Stocks            -5.0 AAPL @ 5.1 USD  ; buy_date:2023-01-01, base_cur:USD
    Asset:Stocks            -1.0 AAPL @ 5.2 USD  ; buy_date:2023-01-05, base_cur:USD
    Revenue:Capital Gain              -8.30 USD
```

#### XIRR

The sale transaction gives you the calculated **xirr** as tag, which is the internal rate of return of an investment based on a specified series of irregularly spaced cash flows. This value is annual percentage rate following the 30/360US day count convention. It is a good metric to compare the investment return with a benchmark like the S&P or the T-Bill, for example.

Note the benchmark can use another day count convention, so this comparison may not be 100% precise. This app may in the future offer others day count convention for **xirr** calculation.


### lots

Generate the report according to the subcommand help:

```
Usage: hledger-fifo lots [OPTIONS]

  Report lots for a commodity.

  Show a report with lots for a commodity considering eventual past sale using
  FIFO accounting principles. Also sum the quantity and calculate average
  price.

  All flags, except '--file' will be interactively prompted if absent, much
  like 'hledger-add'.

Options:
  -f, --file FILENAME   journal file. Without this flag or '-f-', will read
                        from stdin  [required]
  -c, --commodity TEXT  Commodity to get fifo lots
```

#### Output example

```
date          qtty    price    amount  base_cur
----------  ------  -------  --------  ----------
2023-01-05       0   4.0000    0.0000  USD
2023-01-10       4   5.0000   20.0000  USD
2023-01-20      15   5.8000   87.0000  USD

Commodity: AAPL
Total Quantity: 19
Average Cost: 5.63
```

## Limitations

- No _short-selling_
- Each commodity can have only one base currency. For example, it is not possible to buy AAPL with USD and later with EUR.
