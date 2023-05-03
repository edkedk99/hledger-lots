import os
from typing import Literal, Optional, Tuple

import rich_click as click

from .avg_info import AllAvgInfo, AvgInfo
from .fifo_info import AllFifoInfo, FifoInfo
from .files import get_file, get_files_comm
from .info import AllInfo
from .lib import default_fn_bool
from .prices_yahoo import YahooPrices
from .prompt import get_append_file
from .prompt_buy import PromptBuy
from .prompt_sell import PromptSell

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
click.rich_click.ERRORS_EPILOGUE = "To find out more, visit [link=https://github.com/edkedk99/hledger-lots]https://github.com/edkedk99/hledger-lots[/link]"
click.rich_click.STYLE_OPTIONS_TABLE_LEADING = 1
click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE"
click.rich_click.STYLE_OPTIONS_PANEL_BORDER = "dim"  # Possibly conceal


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-f",
    "--file",
    required=False,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.version_option()
def cli(file: Optional[str] = None):  # pyright:ignore
    """
    Commands to apply FIFO(first-in-first-out) or AVERAGE COST accounting principles without manual management of lots. Useful for transactions involving buying and selling foreign currencies or stocks.

    To find out more, visit [https://github.com/edkedk99/hledger-lots](https://github.com/edkedk99/hledger-lots)
    """


@click.command()
@click.option(
    "-f",
    "--file",
    required=False,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-g",
    "--avg-cost",
    is_flag=True,
    default=default_fn_bool("HLEDGER_LOTS_AVG_COST", False),
    help='Change cost method to "average cost"". Can be set with env HLEDGER_LOTS_IS_AVG_COST=true|false. Default to false',
)
@click.option(
    "-n",
    "--no-desc",
    type=click.STRING,
    default=lambda: os.environ.get("HLEDGER_LOTS_NO_DESC", None),
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'. Can be set with env HLEDGER_LOTS_NO_DESC",
)
@click.option(
    "--check/--no-check",
    default=default_fn_bool("HLEDGER_LOTS_CHECK", False),
    help="Enable/Disable check on the commodities previous transactions to ensure it is following the choosen method. Can be set with env HLEDGER_LOTS_CHECK=true|false. Default to false. In the future it will default to true",
)
@click.pass_context
def buy(
    ctx: click.Context,  # pyright:ignore
    avg_cost: bool,
    no_desc: str,
    check: bool,
    file: Tuple[str, ...],
):
    """
    Create a purchase transaction for a commodity by answering some prompts that tries to avoid errors with validation and using current journal data to filter possible answers and give informations that guides the user thru the process.\r

    ### Transaction postings

    - First posting: Negative amount on the cash account where the money was used to pay for the commodity

    - Second Posting: Positive amount of the commodity being bought with its cost using \"@\" symbol
    """

    journals = get_file(ctx, file)
    prompt_buy = PromptBuy(journals, avg_cost, check, no_desc)
    txn_print = prompt_buy.get_hl_txn()
    click.echo("\n" + txn_print)

    append_file = get_append_file(journals[0])
    if append_file:
        with open(append_file, "a") as f:
            f.write("\n" + txn_print)
    else:
        click.echo("\n" + "Transaction not saved.")

    commodity = prompt_buy.info["comm"]
    if avg_cost:
        info = AvgInfo(journals, commodity, check)
    else:
        info = FifoInfo(journals, commodity, check)

    click.echo(info.table)
    click.echo(info.info_txt)

    if commodity.startswith("y."):
        files_comm_str = " ".join(get_files_comm(journals))
        click.echo(
            f"To update prices from Yahoo finance, run:\n\n hledger-lots {files_comm_str} view -c {commodity} -p {journals[0]}"
        )


@click.command()
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    required=False,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-g",
    "--avg-cost",
    is_flag=True,
    default=default_fn_bool("HLEDGER_LOTS_AVG_COST", False),
    help='Change cost method to "average cost"". Can be set with env HLEDGER_LOTS_IS_AVG_COST=true|false. Default to false',
)
@click.option(
    "-n",
    "--no-desc",
    type=click.STRING,
    default=lambda: os.environ.get("HLEDGER_LOTS_NO_DESC", None),
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'. Can be set with env HLEDGER_LOTS_NO_DESC",
)
@click.option(
    "--check/--no-check",
    default=default_fn_bool("HLEDGER_LOTS_CHECK", False),
    help="Enable/Disable check on the commodities previous transactions to ensure it is following the choosen method. Can be set with env HLEDGER_LOTS_CHECK=true|false. Default to false. In the future it will default to true",
)
@click.pass_context
def sell(
    ctx: click.Context,  # pyright:ignore
    avg_cost: bool,
    no_desc: str,
    check: bool,
    file: Tuple[str, ...],
):
    """
    Create a transaction with automatic FIFO or AVERAGE COST for a commodity by answering some prompts that tries to avoid errors with validation and using current journal data to filter possible answers give informations that guides the user thru the process.\r

    > This command also add transaction's comment with some indicators. See an example on "Output examples" page of the docs.

    ### Transaction postings

    - First posting: Positive amount on the 'base-currency' in the account that receives the product of the sale.

    - Multiple lot postings: Each posting represents a lot you are selling for the cost price on purchasing date, according to FIFO accounting principles or one postings in case of AVERAGE COST method.

    - Revenue posting: posting that represent Capital Gain or Loss as the difference between the total cost and the amount received on the base-currency.
    """
    journals = get_file(ctx, file)
    prompt_sell = PromptSell(journals, avg_cost, check, no_desc)

    txn_print = prompt_sell.get_hl_txn()
    click.echo("\n" + txn_print)

    append_file = get_append_file(journals[0])
    if append_file:
        with open(append_file, "a") as f:
            f.write("\n" + txn_print)
    else:
        click.echo("\n" + "Transaction not saved.")

    commodity = prompt_sell.info["comm"]
    if avg_cost:
        info = AvgInfo(journals, commodity, check)
    else:
        info = FifoInfo(journals, commodity, check)

    click.echo(info.table)
    click.echo(info.info_txt)

    if commodity.startswith("y."):
        files_comm_str = " ".join(get_files_comm(journals))
        click.echo(
            f"To update prices from Yahoo finance, run:\n\n hledger-lots {files_comm_str} view -c {commodity} -p {journals[0]}"
        )


@click.command()
@click.option(
    "-f",
    "--file",
    required=False,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-g",
    "--avg-cost",
    is_flag=True,
    default=default_fn_bool("HLEDGER_LOTS_AVG_COST", False),
    help='Change cost method to "average cost"". Can be set with env HLEDGER_LOTS_IS_AVG_COST=true|false. Default to false',
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
    default=lambda: os.environ.get("HLEDGER_LOTS_NO_DESC", None),
    prompt=False,
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'. Can be set with env HLEDGER_LOTS_NO_DESC",
)
@click.option(
    "--check/--no-check",
    default=default_fn_bool("HLEDGER_LOTS_CHECK", False),
    help="Enable/Disable check on the commodities previous transactions to ensure it is following the choosen method. Can be set with env HLEDGER_LOTS_CHECK=true|false. Default to false. Inthe future it will default to true",
)
@click.pass_context
def view(
    ctx: click.Context,
    avg_cost: bool,
    commodity: str,
    no_desc: str,
    check: bool,
    file: Tuple[str, ...],
):
    """
    Report lots for a commodity.\r

    Show a report with lots for a commodity considering eventual past sale using FIFO or AVERAGE COST accounting principles.

    Also show some indicators about the lots and performance if there is prices in the journal after the last purchase. See the docs for details
    """
    journals = get_file(ctx, file)

    if avg_cost:
        info = AvgInfo(journals, commodity, check, no_desc)
    else:
        info = FifoInfo(journals, commodity, check, no_desc)

    click.echo(info.table)
    click.echo(info.info_txt)


@click.command(name="list")
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.option(
    "-g",
    "--avg-cost",
    is_flag=True,
    default=default_fn_bool("HLEDGER_LOTS_AVG_COST", False),
    help='Change cost method to "average cost"". Can be set with env HLEDGER_LOTS_IS_AVG_COST=true|false. Default to false',
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
    default=lambda: os.environ.get("HLEDGER_LOTS_NO_DESC", None),
    prompt=False,
    help="Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: not:desc:<value>. Will not be prompted if absent. If closed with default description, the value of this option should be: 'opening|closing balances'. Can be set with env HLEDGER_LOTS_NO_DESC",
)
@click.option(
    "--check/--no-check",
    default=default_fn_bool("HLEDGER_LOTS_CHECK", False),
    help="Enable/Disable check on the commodities previous transactions to ensure it is following the choosen method. Can be set with env HLEDGER_LOTS_CHECK=tru|false. Default to false. Inthe future it will default to true",
)
@click.pass_context
def list_commodities(
    ctx: click.Context,
    avg_cost: bool,
    output_format: str,
    no_desc: Literal["plain", "pretty", "csv"],
    check: bool,
    file: Tuple[str, ...],
):
    """
    List indicators for all your commodities in a tabular format sorted from higher to lower **XIRR**. It is advised to use full-screen of the terminal. See the docs for a list of indicators and output examples.

    It can output in three formats: *plain, pretty and csv*.
    """

    journals = get_file(ctx, file)
    lots_info = AllInfo(journals, no_desc)

    lots_info = (
        AllAvgInfo(journals, no_desc, check)
        if avg_cost
        else AllFifoInfo(journals, no_desc, check)
    )

    if output_format == "pretty":
        table = lots_info.infos_table("mixed_grid")
    elif output_format == "csv":
        infos_io = lots_info.infos_csv()
        table = infos_io.read()
    else:
        table = lots_info.infos_table("plain")

    click.echo(table)


@click.command()
@click.option(
    "-f",
    "--file",
    required=False,
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.pass_context
def prices(
    ctx: click.Context,  # pyright:ignore
    file: Tuple[str, ...],
):
    """
    Download market prices from Yahoo Finance and print as **price directives**. Use *BASH* redirection to append to the journal or copy/paste the data.

    ### Setup
    Add a \"yahoo_ticker\" tag to the *commodity directive* with the value of the ticker in Yahoo Finance to download prices

    ### Example

    ```text
    commodity AAPL       ; yahoo_ticker:AAPL
    commodity \"PETR4\"    ; yahoo_ticker:PETR4.SA
    commodity BTC        ; yahoo_ticker:BTC-USD
    ```


    """
    yahoo_prices = YahooPrices(file)
    yahoo_prices.print_prices()


cli.add_command(buy)
cli.add_command(sell)
cli.add_command(view)
cli.add_command(list_commodities)
cli.add_command(prices)
