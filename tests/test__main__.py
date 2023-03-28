import pytest
from hledger_fifo import cli

def mock_cli():
    pass



def test_main(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("hledger_fifo.cli.cli", mock_cli)
    cli.cli()
