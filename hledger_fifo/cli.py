from dataclasses import asdict
from typing import Tuple

import rich_click as click
from tabulate import tabulate  # type: ignore

from .fifo import get_lots, get_sell_lots
from .hl import hledger2txn, txn2hl
from .lib import get_default_file, get_file_path
from .lots_info import AllInfo, LotInfo

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.MAX_WIDTH = 80
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = (
    "Try running the '--help' flag for more information."
)
click.rich_click.ERRORS_EPILOGUE = "To find out more, visit [link=https://github.com/edkedk99/hledger-fifo]https://github.com/edkedk99/hledger-fifo[/link]"
click.rich_click.STYLE_OPTIONS_TABLE_LEADING = 1
click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE"
click.rich_click.STYLE_OPTIONS_PANEL_BORDER = "dim"  # Possibly conceal


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=False,
    callback=get_file_path,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.version_option()
def cli(file: str):  # pyright:ignore
    """
    Commands to apply FIFO(first-in-first-out) accounting principles without manual management of lots. Useful for transactions involving buying and selling foreign currencies or stocks.

    To find out more, visit [https://github.com/edkedk99/hledger-fifo](https://github.com/edkedk99/hledger-fifo)
    """


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=False,
    callback=get_file_path,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-c",
    "--commodity",
    type=click.STRING,
    prompt=True,
    help="Commodity to get fifo lots",
)
@click.option(
    "-n",
    "--no-desc",
    type=click.STRING,
    prompt=False,
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'",
)
def lots(file: Tuple[str, ...], commodity: str, no_desc: str):
    """
    Report lots for a commodity.\r

    Show a report with lots for a commodity considering eventual past sale using FIFO accounting principles.

    Also show some indicators about the lots and performance if there is prices in the journal after the last purchase. See the docs for details

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """

    journals = file or get_default_file()
    adj_txn = hledger2txn(journals, commodity, no_desc)
    buy_lots = get_lots(adj_txn)

    lots_dict = [asdict(lot) for lot in buy_lots]
    table = tabulate(
        lots_dict,
        headers="keys",
        numalign="decimal",
        floatfmt=",.4f",
        tablefmt="simple",
    )
    click.echo(table)

    lot_info = LotInfo(file, commodity, buy_lots)
    click.echo(lot_info.info_txt)


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=False,
    callback=get_file_path,
    multiple=True,
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
    "-n",
    "--no-desc",
    type=click.STRING,
    prompt=False,
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'",
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
@click.option(
    "-q",
    "--quantity",
    help="Quantity being sold",
    type=click.FLOAT,
    prompt=True,
)
@click.option(
    "-p",
    "--price",
    help="Price being sold",
    type=click.FLOAT,
    prompt=True,
)
@click.pass_context
def sell(
    ctx: click.Context,  # pyright:ignore
    file: Tuple[str, ...],
    commodity: str,
    no_desc: str,
    cash_account: str,
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

    This command also add transaction's comment with some indicators. See the docs for more info.

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """

    journals = file or get_default_file()
    adj_txns = hledger2txn(journals, commodity, no_desc)
    sell_txn = get_sell_lots(adj_txns, date, quantity)
    value = quantity * price

    txn_print = txn2hl(
        txns=sell_txn,
        date=date,
        cur=commodity,
        cash_account=cash_account,
        revenue_account=revenue_account,
        value=value,
    )
    click.echo(txn_print)


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=False,
    callback=get_file_path,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-o",
    "--output-format",
    type=click.Choice(["plain", "pretty", "csv"]),
    default="plain",
    help="Format to output the report",
)
@click.option(
    "-n",
    "--no-desc",
    type=click.STRING,
    prompt=False,
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'",
)
def info(file: Tuple[str, ...], output_format: str, no_desc: str):
    """
    Show indicators for all your commodities in a tabular format sorted from higher to lower **XIRR**. It is advised to use full-screen of the terminal. See the docs for a list of indicators and output examples.

    It can output in three formats: *plain, pretty and csv*.
    """

    journals = file or get_default_file()
    lots_info = AllInfo(journals, no_desc)

    if output_format == "pretty":
        table = lots_info.get_infos_table("mixed_grid")
    elif output_format == "csv":
        infos_io = lots_info.get_infos_csv()
        table = infos_io.read()
    else:
        table = lots_info.get_infos_table("plain")

    click.echo(table)


cli.add_command(lots)
cli.add_command(sell)
cli.add_command(info)
