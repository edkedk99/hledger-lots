import pytest
from hledger_lots import cli

def mock_cli():
    pass



def test_main(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("hledger_lots.cli.cli", mock_cli)
    cli.cli()
