from typing import Tuple, TypedDict

import rich_click as click

from .avg_info import AllAvgInfo, AvgInfo
from .fifo_info import AllFifoInfo, FifoInfo
from .info import AllInfo
from .lib import get_default_file, get_file_from_stdin, get_files_comm
from .options import Options, get_options
from .prices_yahoo import YahooPrices
from .prompt import get_append_file
from .prompt_buy import PromptBuy
from .prompt_sell import PromptSell


class Obj(TypedDict):
    file: Tuple[str, ...]
    opt: Options


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
    required=True,
    default=lambda: get_default_file(),
    multiple=True,
    help="Inform the journal file path. If \"-\", read from stdin. Without this flag read from $LEDGER_FILE or ~/.hledger.journal in this order  or '-f-'.",
)
@click.pass_obj
@click.version_option()
def cli(obj, file: Tuple[str, ...]):
    """
    Commands to apply FIFO(first-in-first-out) or AVERAGE COST accounting principles without manual management of lots. Useful for transactions involving buying and selling foreign currencies or stocks.

    To find out more, visit [https://github.com/edkedk99/hledger-lots](https://github.com/edkedk99/hledger-lots)
    """

    if file[0] == "-":
        stdin_file = (get_file_from_stdin(),)
        opt = get_options(stdin_file)
        obj["file"] = stdin_file
    else:
        opt = get_options(file)
        obj["file"] = file

    obj["opt"] = opt


@click.command()
@click.pass_obj
def buy(obj: Obj):
    """
    Create a purchase transaction for a commodity by answering some prompts that tries to avoid errors with validation and using current journal data to filter possible answers and give informations that guides the user thru the process.\r

    ### Transaction postings

    - First posting: Negative amount on the cash account where the money was used to pay for the commodity

    - Second Posting: Positive amount of the commodity being bought with its cost using \"@\" symbol
    """

    file = obj["file"]
    opt = obj["opt"]
    prompt_buy = PromptBuy(file, opt.avg_cost, opt.check, opt.no_desc)
    txn_print = prompt_buy.get_hl_txn()
    click.echo("\n" + txn_print)

    append_file = get_append_file(file[0])
    if append_file:
        with open(append_file, "a") as f:
            f.write("\n" + txn_print)
    else:
        click.echo("\n" + "Transaction not saved.")

    commodity = prompt_buy.info["comm"]
    if opt.avg_cost:
        info = AvgInfo(file, commodity, opt.check)
    else:
        info = FifoInfo(file, commodity, opt.check)

    click.echo(info.table)
    click.echo(info.info_txt)


@click.command()
@click.pass_obj
def sell(obj: Obj):
    """
    Create a transaction with automatic FIFO or AVERAGE COST for a commodity by answering some prompts that tries to avoid errors with validation and using current journal data to filter possible answers give informations that guides the user thru the process.\r

    > This command also add transaction's comment with some indicators. See an example on "Output examples" page of the docs.

    ### Transaction postings

    - First posting: Positive amount on the 'base-currency' in the account that receives the product of the sale.

    - Multiple lot postings: Each posting represents a lot you are selling for the cost price on purchasing date, according to FIFO accounting principles or one postings in case of AVERAGE COST method.

    - Revenue posting: posting that represent Capital Gain or Loss as the difference between the total cost and the amount received on the base-currency.
    """
    file = obj["file"]
    opt = obj["opt"]
    prompt_sell = PromptSell(file, opt.avg_cost, opt.check, opt.no_desc)

    txn_print = prompt_sell.get_hl_txn()
    click.echo("\n" + txn_print)

    append_file = get_append_file(file[0])
    if append_file:
        with open(append_file, "a") as f:
            f.write("\n" + txn_print)
    else:
        click.echo("\n" + "Transaction not saved.")

    commodity = prompt_sell.info["comm"]
    if opt.avg_cost:
        info = AvgInfo(file, commodity, opt.check)
    else:
        info = FifoInfo(file, commodity, opt.check)

    click.echo(info.table)
    click.echo(info.info_txt)

    if commodity.startswith("y."):
        files_comm_str = " ".join(get_files_comm(file))
        click.echo(
            f"To update prices from Yahoo finance, run:\n\n hledger-lots {files_comm_str} view -c {commodity} -p {file[0]}"
        )


@click.command()
@click.argument("commodity", type=click.STRING, required=True)
@click.pass_obj
def view(obj: Obj, commodity: str):
    """
    Report lots for a commodity.\r

    Show a report with lots for a commodity considering eventual past sale using FIFO or AVERAGE COST accounting principles.

    Also show some indicators about the lots and performance if there is prices in the journal after the last purchase. See the docs for details
    """
    file = obj["file"]
    opt = obj["opt"]

    if opt.avg_cost:
        info = AvgInfo(file, commodity, opt.check, opt.no_desc)
    else:
        info = FifoInfo(file, commodity, opt.check, opt.no_desc)

    click.echo(info.table)
    click.echo(info.info_txt)


@click.command(name="list")
@click.option(
    "-o",
    "--output-format",
    type=click.Choice(["plain", "pretty", "csv"]),
    default="plain",
    help="Format to output the report",
)
@click.pass_obj
def list_commodities(obj: Obj, output_format: str):
    """
    List indicators for all your commodities in a tabular format sorted from higher to lower **XIRR**. It is advised to use full-screen of the terminal. See the docs for a list of indicators and output examples.

    It can output in three formats: *plain, pretty and csv*.
    """

    file = obj["file"]
    opt = obj["opt"]
    lots_info = AllInfo(file, opt.no_desc)

    lots_info = (
        AllAvgInfo(file, opt.no_desc, opt.check)
        if opt.avg_cost
        else AllFifoInfo(file, opt.no_desc, opt.check)
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
@click.pass_obj
def prices(obj: Obj):
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

    file = obj["file"]

    yahoo_prices = YahooPrices(file)
    yahoo_prices.print_prices()


cli.add_command(buy)
cli.add_command(sell)
cli.add_command(view)
cli.add_command(list_commodities)
cli.add_command(prices)
