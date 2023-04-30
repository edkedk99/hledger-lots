from datetime import datetime
from typing import Optional, Tuple

from .avg import get_avg_cost
from .info import AllInfo, Info, LotsInfo
from .lib import dt_list2table


class AvgInfo(Info):
    def __init__(
        self,
        journals: Tuple[str, ...],
        commodity: str,
        check: bool,
        no_desc: Optional[str] = None,
    ):
        super().__init__(journals, commodity)
        self.check = check
        self.avg_lots = get_avg_cost(self.txns, self.check)
        self.table = dt_list2table(self.avg_lots)

    @property
    def info(self):
        commodity = self.commodity
        cur = self.txns[0].base_cur
        qtty = self.avg_lots[-1].total_qtty
        amount = self.avg_lots[-1].total_amount
        avg_cost = self.avg_lots[-1].avg_cost
        last_buy_date = datetime.strptime(self.avg_lots[-1].date, "%Y-%m-%d").date()
        xirr = self.get_lots_xirr(last_buy_date)

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


class AllAvgInfo(AllInfo):
    def __init__(self, journals: Tuple[str, ...], no_desc: str, check: bool):
        super().__init__(journals, no_desc)
        self.check = check

    def get_info(self, commodity: str):
        avg_obj = AvgInfo(self.journals, commodity, self.check)
        if len(avg_obj.txns) == 0:
            return
        else:
            return avg_obj.info

    @property
    def infos(self):
        infos = [self.get_info(com) for com in self.commodities]
        infos = [info for info in infos if info]
        return infos

    def infos_table(self, output_format: str):
        return self.get_infos_table(self.infos, output_format)

    def infos_csv(self):
        return self.get_infos_csv(self.infos)
