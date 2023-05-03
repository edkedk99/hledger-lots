import re
from typing import List, Tuple, TypedDict


class CommodityTag(TypedDict):
    commodity: str
    value: str


def get_commodity_name(commodity_directive: str):
    commodity = re.sub(r"(\d[,\d.]*\d)|( )|\'|\"", "", commodity_directive)
    return commodity


def get_comment_tag_value(comment: str, tag: str) -> str:
    search = re.search(f"{tag}:\\s?(\\S+)", comment)
    if search and len(search.groups()) == 1:
        return search.group(1)
    else:
        return ""


class CommodityDirective:
    def __init__(self, files: Tuple[str, ...]):
        self.files = files
        self.rows = self.get_commodities_rows()

    def get_commodities_rows(self) -> List[str]:
        rows = []
        for file in self.files:
            with open(file, "r") as f:
                for row in f:
                    if row.startswith("commodity"):
                        rows.append(row)
        return rows

    def get_commodity_tag(self, tag: str):
        regex = re.compile(r"commodity (.+)(;.+)")
        searches = (regex.search(row) for row in self.rows)
        commented_search = (
            search for search in searches if search and len(search.groups()) == 2
        )
        commodities = (
            CommodityTag(
                commodity=get_commodity_name(comment.group(1)),
                value=get_comment_tag_value(comment.group(2), tag),
            )
            for comment in commented_search
        )
        commodities = [
            commodity for commodity in commodities if "" not in commodity.values()
        ]

        return commodities
