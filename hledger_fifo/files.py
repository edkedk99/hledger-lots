import os
from pathlib import Path
from typing import List, Optional, Tuple

import click

ENV_FILE = "LEDGER_FILE"
default_path = Path.home() / ".hledger.journal"


def get_default_file() -> Tuple[str, ...]:
    file_env = os.getenv("LEDGER_FILE")
    if file_env:
        return (file_env,)
    elif default_path.exists():
        return (str(default_path),)
    else:
        raise click.BadOptionUsage("file", "File missing")


def get_file_path(
    ctx: click.Context, _param, value: Optional[Tuple[str, ...]]
) -> Optional[Tuple[str, ...]]:  # type: ignore
    if value:
        return value

    if not ctx.parent:
        return None

    filenames: Optional[Tuple] = ctx.parent.params.get("file")
    if not filenames:
        raise click.BadOptionUsage("file", "File missing")

    return filenames


def get_files_comm(file_path: Tuple[str, ...]) -> List[str]:
    files = []
    for file in file_path:
        files = [*files, "-f", file]
    return files
