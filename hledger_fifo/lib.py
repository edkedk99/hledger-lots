import os
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional
from click import Context, BadOptionUsage


ENV_FILE = "LEDGER_FILE"
default_path = Path.home() / ".hledger.journal"


@dataclass
class AdjustedTxn:
    date: str
    price: float
    base_cur: str
    qtty: float
    acct: str


@dataclass
class Txn(AdjustedTxn):
    type: str


def get_avg(txns: List[AdjustedTxn]):
    total_qtty = sum(txn.qtty for txn in txns)
    mult = [txn.qtty * txn.price for txn in txns]
    total_mult = sum(mult)
    avg = total_mult / total_qtty
    return avg


def get_default_file():
    file_env = os.getenv("LEDGER_FILE")
    if file_env:
        return file_env

    if default_path.exists():
        return str(default_path)


def get_parent_file(ctx:Context) -> str:
    if not ctx.parent:
        raise BadOptionUsage("file", "File missing")

    filename = ctx.parent.params.get("file")
    if not filename:
        raise BadOptionUsage("file", "File missing")

    return filename
        

    
def get_file_path(file_curr: Optional[str], ctx: Context) -> str:
    file_option = file_curr or get_parent_file(ctx)
        
    if file_option != "-":
        return file_option
    else:
        with NamedTemporaryFile(suffix=".journal") as t:
            file_path = t.name
        with open(file_path, "w") as f:
            journal_stdin = sys.stdin
            f.write(journal_stdin.read())
        return file_path

    
