from hledger_lots.lib import AdjustedTxn
import pytest
from hledger_lots import checks


class TestCheckShortSellPast:
    previous_buys = [
        AdjustedTxn(
            date="2022-01-01", price=100.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
        AdjustedTxn(
            date="2022-01-15", price=110.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
        AdjustedTxn(
            date="2022-02-01", price=120.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
    ]

    def test_short_sell_not_allowed(self):
        sell = AdjustedTxn(
            date="2022-03-01", price=100.0, base_cur="USD", qtty=-331, acct="ABC"
        )

        with pytest.raises(ValueError):
            checks.check_short_sell_past(self.previous_buys, sell)

    def test_short_sell_allowed(self):
        sell = AdjustedTxn(
            date="2022-03-01", price=100.0, base_cur="USD", qtty=-100, acct="ABC"
        )
        checks.check_short_sell_past(self.previous_buys, sell)

    def test_empty_previous(self):
        sell = AdjustedTxn(
            date="2022-03-01", price=100.0, base_cur="USD", qtty=-100, acct="ABC"
        )

        with pytest.raises(ValueError):
            checks.check_short_sell_past([], sell)


class TestShortShellCurrent:
    previous_buys = [
        AdjustedTxn(
            date="2022-01-01", price=100.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
        AdjustedTxn(
            date="2022-01-15", price=110.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
        AdjustedTxn(
            date="2022-02-01", price=120.0, base_cur="USD", qtty=50.0, acct="ABC"
        ),
    ]

    def test_sell_less(self):
        checks.check_short_sell_current(self.previous_buys, 140)

    def test_sell_equal(self):
        checks.check_short_sell_current(self.previous_buys, 150)

    def test_sell_more(self):
        with pytest.raises(ValueError):
            checks.check_short_sell_current(self.previous_buys, 160)


class TestCheckBaseCurrency:
    def test_same(self):
        txns = [
            AdjustedTxn(
                date="2022-01-01", price=100.0, base_cur="USD", qtty=50.0, acct="ABC"
            ),
            AdjustedTxn(
                date="2022-01-15", price=110.0, base_cur="USD", qtty=50.0, acct="ABC"
            ),
            AdjustedTxn(
                date="2022-02-01", price=120.0, base_cur="USD", qtty=50.0, acct="ABC"
            ),
        ]
        checks.check_base_currency(txns)

    def test_different(self):

        txns = [
            AdjustedTxn(
                date="2022-01-01",
                price=100.0,
                base_cur="USD",
                qtty=50.0,
                acct="ABC",
            ),
            AdjustedTxn(
                date="2022-01-15",
                price=110.0,
                base_cur="BRL",
                qtty=50.0,
                acct="ABC",
            ),
            AdjustedTxn(
                date="2022-02-01",
                price=120.0,
                base_cur="USD",
                qtty=50.0,
                acct="ABC",
            ),
        ]

        with pytest.raises(checks.MultipleBaseCurrencies):
            checks.check_base_currency(txns)
