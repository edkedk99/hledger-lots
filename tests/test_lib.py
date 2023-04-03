from hledger_lots import lib
from hledger_lots.lib import AdjustedTxn
import pytest
from datetime import date
import pyxirr


class TestGetAvg:
    def test_empty_list(self):
        assert lib.get_avg_fifo([]) == 0

    def test_single_txn(self):
        txn = AdjustedTxn(
            date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
        )
        assert lib.get_avg_fifo([txn]) == 100.0

    def test_multiple_txns(self):
        txns = [
            AdjustedTxn(
                date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-02", price=150.0, base_cur="USD", qtty=5.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-03", price=200.0, base_cur="USD", qtty=20.0, acct="1234"
            ),
        ]
        assert lib.get_avg_fifo(txns) == pytest.approx(164.28, abs=1e-2)

    def test_zero_quantity(self):
        txns = [
            AdjustedTxn(
                date="2022-01-01", price=100.0, base_cur="USD", qtty=10.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-02", price=150.0, base_cur="USD", qtty=0.0, acct="1234"
            ),
            AdjustedTxn(
                date="2022-01-03", price=200.0, base_cur="USD", qtty=20.0, acct="1234"
            ),
        ]
        assert lib.get_avg_fifo(txns) == pytest.approx(166.67, abs=1e-2)



class TestGetXirr:
    txns = [
            AdjustedTxn("2023-01-23", 100, "USD", -1, "acct"),
            AdjustedTxn("2023-02-23", 100, "USD", -1, "acct"),
        ]
    
    def test_xirr_ok(self):
        assert lib.get_xirr(101,date(2023,3,23),self.txns) == pytest.approx(0.0828, abs=1e-4)

    def test_xirr_only_negatives(self):
        with pytest.raises(pyxirr.InvalidPaymentsError):
            lib.get_xirr(0,date(2023,3,23),self.txns)

    def test_xirr_empty(self):
        lib.get_xirr(0,date(2023,3,23),[]) == None

    def test_xir_negative(self):
        assert lib.get_xirr(99,date(2023,3,23),self.txns) == pytest.approx(-0.0772, abs=1e-4)
        


        
        
