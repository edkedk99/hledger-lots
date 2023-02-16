import click
from tabulate import tabulate  # type: ignore

from .fifo import get_lots, get_sell_lots
from .hl import hledger2txn, txn2hl
from .lib import get_avg, get_default_file, get_file_path

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Commands to apply FIFO(first-in-first-out) accounting principles without manual management of lots. Useful for transactions involving purchase and selling foreign currencies or stocks.
    """


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=True,
    default=get_default_file(),
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-c",
    "--commodity",
    type=click.STRING,
    prompt=True,
    help="Commodity to get fifo lots",
)
def lots(file: str, commodity: str):
    """
    Report lots for a commodity.\r

    Show a report with lots for a commodity considering eventual past sale using FIFO accounting principles. Also sum the quantity and calculate average price.

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """

    file_path = get_file_path(file)
    adj_txn = hledger2txn(file_path, commodity)
    buy_lots = get_lots(adj_txn)

    lots_dict = [
        dict(
            date=lot.date,
            qtty=lot.qtty,
            price=lot.price,
            amount=lot.price * lot.qtty,
            base_cur=lot.base_cur,
        )
        for lot in buy_lots
    ]
    table = tabulate(
        lots_dict,
        headers="keys",
        numalign="decimal",
        floatfmt=",.4f",
        tablefmt="simple",
    )
    click.echo(table)
    total_qtty = sum(lot.qtty for lot in buy_lots)
    avg = get_avg(buy_lots) if total_qtty > 0 else 0

    click.echo(f"\nCommodity: {commodity}")
    click.echo(f"Total Quantity: {total_qtty}")
    click.echo(f"Average Cost: {avg:,.2f}")


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=True,
    default=get_default_file(),
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-c",
    "--commodity",
    type=click.STRING,
    prompt=True,
    help="Commodity you are selling",
)
@click.option(
    "-b",
    "--base-currency",
    type=click.STRING,
    prompt=True,
    help="Currency on which you are receiving for the sale",
)
@click.option(
    "-a",
    "--cash-account",
    type=click.STRING,
    prompt=True,
    help="What account entered the product of the sell",
)
@click.option(
    "-r",
    "--revenue-account",
    type=click.STRING,
    prompt=True,
    help="Account that represent capital gain/loss",
)
@click.option(
    "-d",
    "--date",
    type=click.STRING,
    prompt=True,
    help="Date of the transaction (YYYY-mm-dd)",
)
@click.option("-q", "--quantity", type=click.FLOAT, prompt=True)
@click.option("-p", "--price", type=click.FLOAT, prompt=True)
def sell(
    file: str,
    commodity: str,
    cash_account: str,
    base_currency: str,
    revenue_account: str,
    date: str,
    quantity: float,
    price: float,
):
    """
    Create a transaction with automatic FIFO for a commodity.\r

    Generate a transaction that represents a sale of a commodity with the following postings:

    - First posting: Positive amount on the 'base-currency' in the account that receives the product of the sale.

    - Multiple lot postings: Each posting is a different lot you are selling for the cost price on purchasing date, calculated according to FIFO accounting principles.

    - Revenue posting: posting that represent Capital Gain or Loss as the difference between the total cost and the amount received on the base-currency.

    This command also add transaction's comment with the following information as tags: commodity, total quantity sold and average FIFO cost

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """
    file_path = get_file_path(file)
    adj_txns = hledger2txn(file_path, commodity)
    sell_txn = get_sell_lots(adj_txns, date, quantity)

    value = price * quantity
    txn_print = txn2hl(
        sell_txn,
        date,
        commodity,
        cash_account,
        revenue_account,
        base_currency,
        value,
    )
    click.echo(txn_print)


cli.add_command(lots)
cli.add_command(sell)
