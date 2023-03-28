from hledger_fifo.lib import AdjustedTxn
from hledger_fifo import fifo
import pytest
from . import lots_data


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
            fifo.check_short_sell_past(self.previous_buys, sell)

    def test_short_sell_allowed(self):
        sell = AdjustedTxn(
            date="2022-03-01", price=100.0, base_cur="USD", qtty=-100, acct="ABC"
        )
        fifo.check_short_sell_past(self.previous_buys, sell)

    def test_empty_previous(self):
        sell = AdjustedTxn(
            date="2022-03-01", price=100.0, base_cur="USD", qtty=-100, acct="ABC"
        )

        with pytest.raises(ValueError):
            fifo.check_short_sell_past([], sell)


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
        fifo.check_short_sell_current(self.previous_buys, 140)

    def test_sell_equal(self):
        fifo.check_short_sell_current(self.previous_buys, 150)

    def test_sell_more(self):
        with pytest.raises(ValueError):
            fifo.check_short_sell_current(self.previous_buys, 160)


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
        fifo.check_base_currency(txns)

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

        with pytest.raises(fifo.MultipleBaseCurrencies):
            fifo.check_base_currency(txns)


class TestGetLots:
    def test_only_buying(self):
        assert fifo.get_lots(lots_data.txns_only_buying) == lots_data.txns_only_buying

    def test_never_zero(self):
        assert (
            fifo.get_lots(lots_data.txns_qtty_never_zero)
            == lots_data.expected_qtty_never_zero
        )

    def test_qtty_reach_zero(self):
        assert (
            fifo.get_lots(lots_data.txns_qtty_reaches_zero)
            == lots_data.expected_qtty_reaches_zero
        )


class TestGetSellLots:
    def test_sell_all(self):
        sell_lots = fifo.get_sell_lots(
            lots_data.txns_qtty_reaches_zero, sell_date="2022-02-01", sell_qtty=5
        )
        assert sell_lots == lots_data.expected_qtty_reaches_zero_sell_all

    def test_sell_some(self):
        sell_lots = fifo.get_sell_lots(
            lots_data.txns_qtty_never_zero, sell_date="2022-02-01", sell_qtty=11
        )
        assert sell_lots == lots_data.expected_qtty_never_zero_sell_some
