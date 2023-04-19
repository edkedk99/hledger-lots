from hledger_lots import fifo

from . import lots_data


class TestGetLots:
    def test_only_buying(self):
        assert (
            fifo.get_lots(lots_data.txns_only_buying, check=False)
            == lots_data.txns_only_buying
        )

    def test_never_zero(self):
        assert (
            fifo.get_lots(lots_data.txns_qtty_never_zero, check=False)
            == lots_data.expected_qtty_never_zero
        )

    def test_qtty_reach_zero(self):
        assert (
            fifo.get_lots(lots_data.txns_qtty_reaches_zero, check=False)
            == lots_data.expected_qtty_reaches_zero
        )


class TestGetSellLots:
    def test_sell_all(self):
        sell_lots = fifo.get_sell_lots(
            lots_data.txns_qtty_reaches_zero,
            sell_date="2022-02-01",
            sell_qtty=5,
            check=False,
        )
        assert sell_lots == lots_data.expected_qtty_reaches_zero_sell_all

    def test_sell_some(self):
        sell_lots = fifo.get_sell_lots(
            lots_data.txns_qtty_never_zero,
            sell_date="2022-02-01",
            sell_qtty=11,
            check=False,
        )
        assert sell_lots == lots_data.expected_qtty_never_zero_sell_some


class TestTxn2Hl:
    txns = lots_data.expected_qtty_reaches_zero_sell_all
    date = "2022-02-01"
    cash_account = "Bank"
    revenue_account = "Revenue"

    def test_txn2hl_profit(self):
        cur = "USD"
        test = fifo.txn2hl(
            self.txns, self.date, cur, self.cash_account, self.revenue_account, 160)

        expected = """2022-02-01 Sold USD  ; cost_method:fifo
    ; commodity:USD, qtty:5.00, price:32.00
    ; avg_cost:26.0000, xirr:61.42% annual percent rate 30/360US
    Bank                 160.00 USD
    Acct1      -2.00 USD @ 35.0 USD  ; buy_date:2022-01-12, base_cur:USD
    Acct1      -3.00 USD @ 20.0 USD  ; buy_date:2022-01-14, base_cur:USD
    Revenue              -30.00 USD

"""

        assert test == expected

    def test_txn2hl_loss(self):
        cur = "USD"
        test = fifo.txn2hl(
            self.txns, self.date, cur, self.cash_account, self.revenue_account, 80
        )

        expected = """2022-02-01 Sold USD  ; cost_method:fifo
    ; commodity:USD, qtty:5.00, price:16.00
    ; avg_cost:26.0000, xirr:-1.00% annual percent rate 30/360US
    Bank                  80.00 USD
    Acct1      -2.00 USD @ 35.0 USD  ; buy_date:2022-01-12, base_cur:USD
    Acct1      -3.00 USD @ 20.0 USD  ; buy_date:2022-01-14, base_cur:USD
    Revenue               50.00 USD

"""

        assert test == expected
