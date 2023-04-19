from hledger_lots.avg import get_avg_cost, avg_sell, AvgCost
from datetime import date
from . import lots_data


class TestGetAvgCost:
    def test_empty(self):
        assert get_avg_cost([], False, date(2022, 1, 1)) == []

    def test_only_buying_after_some(self):
        txns = lots_data.txns_only_buying
        expected = [
            AvgCost(
                date="2022-01-01", total_qtty=10.0, total_amount=100.0, avg_cost=10.0
            ),
            AvgCost(
                date="2022-01-02",
                total_qtty=12.0,
                total_amount=140.0,
                avg_cost=11.666666666666666,
            ),
            AvgCost(
                date="2022-01-03",
                total_qtty=17.0,
                total_amount=290.0,
                avg_cost=17.058823529411764,
            ),
            AvgCost(
                date="2022-01-04",
                total_qtty=65.0,
                total_amount=1010.0,
                avg_cost=15.538461538461538,
            ),
        ]

        assert get_avg_cost(txns, False,date(2022, 1, 4)) == expected

    def test_only_buying_after_all(self):
        txns = lots_data.txns_only_buying
        expected = [
            AvgCost(
                date="2022-01-01", total_qtty=10.0, total_amount=100.0, avg_cost=10.0
            ),
            AvgCost(
                date="2022-01-02",
                total_qtty=12.0,
                total_amount=140.0,
                avg_cost=11.666666666666666,
            ),
            AvgCost(
                date="2022-01-03",
                total_qtty=17.0,
                total_amount=290.0,
                avg_cost=17.058823529411764,
            ),
            AvgCost(
                date="2022-01-04",
                total_qtty=65.0,
                total_amount=1010.0,
                avg_cost=15.538461538461538,
            ),
            AvgCost(
                date="2022-01-05",
                total_qtty=86.0,
                total_amount=1535.0,
                avg_cost=17.848837209302324,
            ),
        ]

        assert get_avg_cost(txns, False) == expected

    def test_with_sell(self):
        txns = lots_data.txns_qtty_never_zero
        expected = [
            AvgCost(
                date="2022-01-01", total_qtty=5.0, total_amount=50.0, avg_cost=10.0
            ),
            AvgCost(
                date="2022-01-02",
                total_qtty=7.0,
                total_amount=90.0,
                avg_cost=12.857142857142858,
            ),
            AvgCost(
                date="2022-01-03",
                total_qtty=14.0,
                total_amount=300.0,
                avg_cost=21.428571428571427,
            ),
            AvgCost(
                date="2022-01-04",
                total_qtty=11.0,
                total_amount=235.71428571428572,
                avg_cost=21.42857142857143,
            ),
            AvgCost(
                date="2022-01-05",
                total_qtty=13.0,
                total_amount=285.7142857142857,
                avg_cost=21.978021978021978,
            ),
            AvgCost(
                date="2022-01-06",
                total_qtty=18.0,
                total_amount=460.7142857142857,
                avg_cost=25.595238095238095,
            ),
            AvgCost(
                date="2022-01-07",
                total_qtty=13.0,
                total_amount=332.73809523809524,
                avg_cost=25.595238095238095,
            ),
            AvgCost(
                date="2022-01-08",
                total_qtty=15.0,
                total_amount=372.73809523809524,
                avg_cost=24.849206349206348,
            ),
        ]

        assert get_avg_cost(txns, False,date(2022, 1, 8)) == expected


class TestAvgSell:
    def test_avg_sell(self):
        txns = lots_data.txns_only_buying
        test = avg_sell(
            txns=txns,
            date="2022-02-01",
            qtty=50,
            cur="AAPL",
            cash_account="Asset:Bank",
            revenue_account="Revenue:Capital Gain",
            comm_account="Acct1",
            value=1000,
            check=False,
        )

        expected = """2022-02-01 Sold AAPL  ; cost_method:avg_cost
    ; commodity:AAPL, qtty:50.00, price:20.00
    ; xirr:3.56% annual percent rate 30/360US
    Asset:Bank                                    1000.00 USD
    Acct1                   -50 AAPL @ 17.848837209302324 USD
    Revenue:Capital Gain               -107.5581395348838 USD

"""

        assert test == expected
