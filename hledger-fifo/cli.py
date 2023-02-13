import sys
from io import TextIOWrapper

import click
from tabulate import tabulate  # type: ignore

from .fifo import get_lots, get_sell_lots
from .hl import hledger2txn, txn2hl
from .lib import get_avg


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.File(mode="r", encoding="utf8"),
    required=True,
    default=sys.stdin,
    help="journal file",
)
@click.option(
    "-c",
    "--currency",
    type=click.STRING,
    prompt=True,
)
def lots(file: TextIOWrapper, currency: str):
    adj_txn = hledger2txn(file, currency)
    buy_lots = get_lots(adj_txn)

    lots_dict = [
        dict(
            date=lot.date,
            price=lot.price,
            qtty=lot.qtty,
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
    avg = get_avg(buy_lots)
    click.echo(f"\nAverage Cost: {avg:,.2f}")


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.File(mode="r", encoding="utf8"),
    required=True,
    default=sys.stdin,
    help="journal file",
)
@click.option("-c", "--currency", type=click.STRING, prompt=True)
@click.option("-b", "--base-currency", type=click.STRING, prompt=True)
@click.option("-a", "--cash-account", type=click.STRING, prompt=True)
@click.option("-r", "--revenue-account", type=click.STRING, prompt=True)
@click.option("-d", "--date", type=click.STRING, prompt=True)
@click.option("-q", "--quantity", type=click.FLOAT, prompt=True)
@click.option("-p", "--price", type=click.FLOAT, prompt=True)
def sell(
    file: TextIOWrapper,
    currency: str,
    cash_account: str,
    base_currency: str,
    revenue_account: str,
    date: str,
    quantity: float,
    price: float,
):
    adj_txns = hledger2txn(file, currency)
    sell_txn = get_sell_lots(adj_txns, date, quantity)

    value = price * quantity
    txn_print = txn2hl(
        sell_txn,
        date,
        currency,
        cash_account,
        revenue_account,
        base_currency,
        value,
    )
    click.echo(txn_print)


cli.add_command(lots)
cli.add_command(sell)
