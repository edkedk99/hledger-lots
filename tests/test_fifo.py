from hledger_fifo import fifo

from . import lots_data


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
