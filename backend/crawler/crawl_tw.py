import csv
import datetime as dt
import io
import logging
import zipfile
from typing import Dict, Iterator, List, Optional

from .base_spider import BaseSpider

CITY_CODE = {
    "A": "\u81fa\u5317\u5e02",  # Taipei City
    "B": "\u81fa\u4e2d\u5e02",  # Taichung City
    "D": "\u81fa\u5357\u5e02",  # Tainan City
    "E": "\u9ad8\u96c4\u5e02",  # Kaohsiung City
    "F": "\u65b0\u5317\u5e02",  # New Taipei City
    "H": "\u6843\u5712\u5e02",  # Taoyuan City
}

COL_TOTAL_PRICE = "\u7e3d\u50f9\u5143"
COL_UNIT_PRICE = "\u55ae\u50f9\u5143\u5e73\u65b9\u516c\u5c3a"
COL_AREA = "\u5efa\u7269\u79fb\u8f49\u7e3d\u9762\u7a4d\u5e73\u65b9\u516c\u5c3a"
COL_REGION = "\u9109\u93ae\u5e02\u5340"
COL_ADDRESS = "\u571f\u5730\u5340\u6bb5\u4f4d\u7f6e\u5efa\u7269\u5340\u6bb5\u9580\u724c"
COL_TYPE = "\u5efa\u7269\u578b\u614b"
COL_USAGE = "\u4e3b\u8981\u7528\u9014"
COL_BUILD_YEAR = "\u5efa\u7bc9\u5b8c\u6210\u5e74\u6708"
COL_DEAL_DATE = "\u4ea4\u6613\u5e74\u6708\u65e5"


class TaiwanRealPriceSpider(BaseSpider):
    """Download open-data ZIP and emit normalized real-price rows."""

    def __init__(self, city_code: str = "A", year_month: Optional[str] = None, **kwargs) -> None:
        super().__init__("https://plvr.land.moi.gov.tw", **kwargs)
        self.city_code = city_code.upper()
        self.city_name = CITY_CODE.get(self.city_code, self.city_code)
        self.year_month = year_month or dt.date.today().strftime("%Y%m")
        self.logger = logging.getLogger(self.__class__.__name__)

    def _zip_url(self) -> str:
        # Official open-data URL bundles all cities; filter by file prefix (A/B/D/E/F/H...)
        return f"{self.base_url}/Download?type=zip&fileName=lvr_landcsv.zip"

    def _parse_date(self, roc_date: str) -> str:
        roc_date = roc_date.strip()
        if not roc_date:
            return ""
        if len(roc_date) < 5:  # e.g., "11201"
            roc_date = roc_date.ljust(5, "0")
        year = 1911 + int(roc_date[:3])
        month = roc_date[3:5] or "01"
        day = roc_date[5:7] if len(roc_date) >= 7 else "01"
        return f"{year:04d}-{int(month):02d}-{int(day):02d}"

    def _normalize_row(self, row: Dict[str, str]) -> Dict:
        total_price = self.to_float(row.get(COL_TOTAL_PRICE))
        unit_price = self.to_float(row.get(COL_UNIT_PRICE))
        area = self.to_float(row.get(COL_AREA))
        return {
            "source": "taiwan_real_price",
            "city": self.city_name,
            "region": row.get(COL_REGION),
            "raw_address": row.get(COL_ADDRESS),
            "house_type": row.get(COL_TYPE),
            "usage": row.get(COL_USAGE),
            "build_year": row.get(COL_BUILD_YEAR),
            "deal_date": self._parse_date(row.get(COL_DEAL_DATE, "")),
            "total_price_ntd": total_price,
            "unit_price_ntd_sqm": unit_price,
            "area_sqm": area,
        }

    def crawl(self) -> Iterator[Dict]:
        url = self._zip_url()
        resp = self.get(url)
        if not resp:
            self.logger.error("Failed to download ZIP")
            return iter(())

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            target_files = [name for name in zf.namelist() if name.lower().startswith(self.city_code.lower()) and name.lower().endswith(".csv")]
            if not target_files:
                self.logger.error("No CSV found for city code %s", self.city_code)
                return iter(())

            for name in target_files:
                with zf.open(name) as fp:
                    text = io.TextIOWrapper(fp, encoding="utf-8-sig")
                    reader = csv.DictReader(text)
                    for row in reader:
                        if not row.get(COL_REGION):
                            continue
                        yield self._normalize_row(row)

    def run(self) -> None:
        count = 0
        for row in self.crawl():
            count += 1
            if count <= 5:
                self.logger.info("Deal: %s | %s | %s NTD", row["region"], row["deal_date"], row["total_price_ntd"])
        self.logger.info("Total rows fetched: %s", count)


if __name__ == "__main__":
    spider = TaiwanRealPriceSpider(city_code="A", delay_range=(0.5, 1.5))
    spider.run()
