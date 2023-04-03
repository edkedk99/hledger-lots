from hledger_lots.lib import AdjustedTxn

txns_only_buying = [
    AdjustedTxn(date="2022-01-01", price=10.0, base_cur="USD", qtty=10.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-02", price=20.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-03", price=30.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-04", price=15.0, base_cur="USD", qtty=48.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-05", price=25.0, base_cur="USD", qtty=21.0, acct="Acct1"),
]


txns_qtty_never_zero = [
    AdjustedTxn(date="2022-01-01", price=10.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-02", price=20.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-03", price=30.0, base_cur="USD", qtty=7.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-04", price=15.0, base_cur="USD", qtty=-3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-05", price=25.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-06", price=35.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-07", price=10.0, base_cur="USD", qtty=-5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-08", price=20.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-09", price=30.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-10", price=15.0, base_cur="USD", qtty=-4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-11", price=25.0, base_cur="USD", qtty=3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-12", price=35.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-13", price=10.0, base_cur="USD", qtty=-5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-14", price=20.0, base_cur="USD", qtty=3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-15", price=30.0, base_cur="USD", qtty=2.0, acct="Acct1"),
]


expected_qtty_never_zero = [
    AdjustedTxn(date="2022-01-01", price=10.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-02", price=20.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-03", price=30.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-05", price=25.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-06", price=35.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-08", price=20.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-09", price=30.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-11", price=25.0, base_cur="USD", qtty=3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-12", price=35.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-14", price=20.0, base_cur="USD", qtty=3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-15", price=30.0, base_cur="USD", qtty=2.0, acct="Acct1"),
]

expected_qtty_never_zero_sell_some = [
    AdjustedTxn(date='2022-01-06', price=35.0, base_cur='USD', qtty=4.0, acct='Acct1'),
    AdjustedTxn(date='2022-01-08', price=20.0, base_cur='USD', qtty=2.0, acct='Acct1'),
    AdjustedTxn(date='2022-01-09', price=30.0, base_cur='USD', qtty=4.0, acct='Acct1'),
    AdjustedTxn(date='2022-01-11', price=25.0, base_cur='USD', qtty=1.0, acct='Acct1')
]


txns_qtty_reaches_zero = [
    AdjustedTxn(date="2022-01-01", price=10.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-02", price=20.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-03", price=30.0, base_cur="USD", qtty=-3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-04", price=15.0, base_cur="USD", qtty=4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-05", price=25.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-06", price=35.0, base_cur="USD", qtty=-1.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-07", price=10.0, base_cur="USD", qtty=-4.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-08", price=20.0, base_cur="USD", qtty=-5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-09", price=30.0, base_cur="USD", qtty=10.0, acct="Acct1"),
    AdjustedTxn(
        date="2022-01-10", price=15.0, base_cur="USD", qtty=-10.0, acct="Acct1"
    ),
    AdjustedTxn(date="2022-01-11", price=25.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-12", price=35.0, base_cur="USD", qtty=5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-13", price=10.0, base_cur="USD", qtty=-5.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-14", price=20.0, base_cur="USD", qtty=3.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-15", price=30.0, base_cur="USD", qtty=-3.0, acct="Acct1"),
]

expected_qtty_reaches_zero = [
    AdjustedTxn(date="2022-01-01", price=10.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-02", price=20.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-04", price=15.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-05", price=25.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-09", price=30.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-11", price=25.0, base_cur="USD", qtty=0, acct="Acct1"),
    AdjustedTxn(date="2022-01-12", price=35.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-14", price=20.0, base_cur="USD", qtty=3.0, acct="Acct1"),
]

expected_qtty_reaches_zero_sell_all = [
    AdjustedTxn(date="2022-01-12", price=35.0, base_cur="USD", qtty=2.0, acct="Acct1"),
    AdjustedTxn(date="2022-01-14", price=20.0, base_cur="USD", qtty=3.0, acct="Acct1"),
]
