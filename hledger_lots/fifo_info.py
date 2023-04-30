from datetime import datetime
from typing import Optional, Tuple

from .checks import MultipleBaseCurrencies
from .fifo import get_lots
from .hl import hledger2txn
from .info import AllInfo, Info, LotsInfo
from .lib import dt_list2table, get_avg_fifo


class FifoInfo(Info):
    def __init__(
        self,
        journals: Tuple[str, ...],
        commodity: str,
        check: bool,
        no_desc: Optional[str] = None,
    ):
        super().__init__(journals, commodity)
        self.check = check

        self.lots = get_lots(self.txns, check)
        self.last_buy_date = self.lots[-1].date if len(self.lots) > 0 else None

        self.buy_lots = get_lots(self.txns, check)
        self.table = dt_list2table(self.buy_lots)

    @property
    def info(self):
        commodity = self.commodity

        cur = self.lots[0].base_cur
        qtty = sum(lot.qtty for lot in self.lots)
        amount = sum(lot.price * lot.qtty for lot in self.lots)
        avg_cost = get_avg_fifo(self.lots) if qtty > 0 else 0

        if self.has_txn:
            last_buy_date_str = self.lots[-1].date
            last_buy_date = datetime.strptime(last_buy_date_str, "%Y-%m-%d").date()
            xirr = self.get_lots_xirr(last_buy_date)
        else:
            xirr = 0

        if self.market_price and self.market_date and xirr:
            market_price_str = f"{self.market_price:,.4f}"
            market_amount = self.market_price * qtty
            market_amount_str = f"{market_amount:,.2f}"
            market_profit = market_amount - amount
            market_profit_str = f"{market_profit:,.2f}"
            market_date = self.market_date.strftime("%Y-%m-%d")

            xirr_str = f"{xirr:,.4f}%"
        else:
            market_amount_str = ""
            market_profit_str = ""
            market_date = ""
            market_price_str = ""
            xirr_str = ""

        return LotsInfo(
            comm=commodity,
            cur=cur,
            qtty=str(qtty),
            amount=f"{amount:,.2f}",
            avg_cost=f"{avg_cost:,.4f}",
            mkt_price=market_price_str,
            mkt_amount=market_amount_str,
            mkt_profit=market_profit_str,
            mkt_date=market_date,
            xirr=xirr_str,
        )

    @property
    def info_txt(self):
        return self.get_info_txt(self.info)


class AllFifoInfo(AllInfo):
    def __init__(self, journals: Tuple[str, ...], no_desc: str, check: bool):
        super().__init__(journals, no_desc)
        self.check = check

    def get_info(self, commodity: str):
        txns = hledger2txn(self.journals, commodity, self.no_desc)
        try:
            lots = get_lots(txns, self.check)
        except MultipleBaseCurrencies:
            return None

        if len(lots) > 0:
            lot_info = FifoInfo(self.journals, commodity, self.check).info
            return lot_info

    @property
    def infos(self):
        infos = [self.get_info(com) for com in self.commodities]
        infos = [info for info in infos if info is not None]
        return infos

    def infos_table(self, output_format: str):
        return self.get_infos_table(self.infos, output_format)

    def infos_csv(self):
        return self.get_infos_csv(self.infos)
