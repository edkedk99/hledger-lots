from typing import Literal, Tuple

import rich_click as click

from .avg import avg_sell, get_avg_cost
from .avg_info import AllAvgInfo, AvgInfo
from .fifo import get_lots, get_sell_lots, txn2hl
from .fifo_info import AllFifoInfo, FifoInfo
from .files import get_default_file, get_file_path
from .hl import hledger2txn
from .info import AllInfo
from .lib import dt_list2table

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
    Commands to apply FIFO(first-in-first-out) or AVERAGE COST accounting principles without manual management of lots. Useful for transactions involving buying and selling foreign currencies or stocks.

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
    "-g", "--avg-cost", is_flag=True, help='Change cost method to "average cost"'
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
def view(file: Tuple[str, ...], avg_cost: bool, commodity: str, no_desc: str):
    """
    Report lots for a commodity.\r

    Show a report with lots for a commodity considering eventual past sale using FIFO or AVERAGE COST accounting principles.

    Also show some indicators about the lots and performance if there is prices in the journal after the last purchase. See the docs for details

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """

    journals = file or get_default_file()
    adj_txn = hledger2txn(journals, commodity, no_desc)

    if avg_cost:
        buy_lots = get_avg_cost(adj_txn)
        table = dt_list2table(buy_lots)
        click.echo(table)
        avg_info = AvgInfo(journals, commodity)
        click.echo(avg_info.info_txt)

    else:
        buy_lots = get_lots(adj_txn)
        table = dt_list2table(buy_lots)
        click.echo(table)
        fifo_info = FifoInfo(journals, commodity)
        click.echo(fifo_info.info_txt)


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
    "-g", "--avg-cost", is_flag=True, help='Change cost method to "average cost"'
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
    "-s",
    "--commodity-account",
    type=click.STRING,
    prompt=False,
    required=False,
    help="What account holds product of the sale. Only used with --avg-cost",
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
    avg_cost: bool,
    commodity: str,
    no_desc: str,
    commodity_account: str,
    cash_account: str,
    revenue_account: str,
    date: str,
    quantity: float,
    price: float,
):
    """
    Create a transaction with automatic FIFO or AVERAGE COST for a commodity.\r

    Generate a transaction that represents a sale of a commodity with the following postings:

    - First posting: Positive amount on the 'base-currency' in the account that receives the product of the sale.

    - Multiple lot postings: Each posting is a different lot you are selling for the cost price on purchasing date, calculated according to FIFO accounting principles.

    - Revenue posting: posting that represent Capital Gain or Loss as the difference between the total cost and the amount received on the base-currency.

    This command also add transaction's comment with some indicators. See the docs for more info.

    All flags, except '--file' will be interactively prompted if absent, much like 'hledger-add'.
    """

    journals = file or get_default_file()
    adj_txns = hledger2txn(journals, commodity, no_desc)
    value = quantity * price

    if avg_cost and not commodity_account:
        commodity_account = input("Commodity account")

    if avg_cost:
        sell_avg = avg_sell(
            txns=adj_txns,
            date=date,
            qtty=quantity,
            cur=commodity,
            cash_account=cash_account,
            revenue_account=revenue_account,
            comm_account=commodity_account,
            value=value,
        )
        click.echo(sell_avg)
    else:
        sell_fifo = get_sell_lots(adj_txns, date, quantity)
        txn_print = txn2hl(
            txns=sell_fifo,
            date=date,
            cur=commodity,
            cash_account=cash_account,
            revenue_account=revenue_account,
            value=value,
        )
        click.echo(txn_print)


@click.command(name="list")
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
    "-g", "--avg-cost", is_flag=True, help='Change cost method to "average cost"'
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
def list_commodities(
    file: Tuple[str, ...],
    avg_cost: bool,
    output_format: str,
    no_desc: Literal["plain", "pretty", "csv"],
):
    """
    List indicators for all your commodities in a tabular format sorted from higher to lower **XIRR**. It is advised to use full-screen of the terminal. See the docs for a list of indicators and output examples.

    It can output in three formats: *plain, pretty and csv*.
    """

    journals = file or get_default_file()
    lots_info = AllInfo(journals, no_desc)

    lots_info = AllAvgInfo(file, no_desc) if avg_cost else AllFifoInfo(file, no_desc)

    if output_format == "pretty":
        table = lots_info.infos_table("mixed_grid")
    elif output_format == "csv":
        infos_io = lots_info.infos_csv()
        table = infos_io.read()
    else:
        table = lots_info.infos_table("plain")

    click.echo(table)


cli.add_command(view)
cli.add_command(sell)
cli.add_command(list_commodities)
