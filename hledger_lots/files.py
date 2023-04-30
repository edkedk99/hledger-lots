import os
from pathlib import Path
from typing import List, Optional, Tuple

import click

ENV_FILE = "LEDGER_FILE"
default_path = Path.home() / ".hledger.journal"


def get_parent_file(ctx: click.Context):
    parent = ctx.parent
    if not parent:
        return None

    file_parent = parent.params.get("file")
    if not file_parent:
        return None
    file: Optional[Tuple[str, ...]] = file_parent
    return file


def get_file(ctx: click.Context, file: Tuple[str, ...]):
    if len(file) > 0:
        return file

    parent_file = get_parent_file(ctx)
    if parent_file:
        return parent_file

    env_file = os.getenv("LEDGER_FILE")
    if env_file:
        return (env_file,)

    raise click.BadOptionUsage("file", "File missing")


def get_files_comm(file_path: Tuple[str, ...]) -> List[str]:
    files = []
    for file in file_path:
        files = [*files, "-f", file]
    return files
