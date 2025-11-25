import logging
from typing import Dict, Iterator, List, Optional

from .base_spider import BaseSpider


class LianjiaSpider(BaseSpider):
    """Crawl Lianjia ershoufang listings and chengjiao transactions."""

    def __init__(
        self,
        city: str = "bj",
        region: Optional[str] = None,
        pages: int = 2,
        **kwargs,
    ) -> None:
        super().__init__(f"https://{city}.lianjia.com", **kwargs)
        self.city = city
        self.region = region.strip("/") if region else ""
        self.pages = pages
        self.logger = logging.getLogger(self.__class__.__name__)

    def _listing_url(self, page: int) -> str:
        path = f"/ershoufang/{self.region}/" if self.region else "/ershoufang/"
        return f"{self.base_url}{path}pg{page}/"

    def _transaction_url(self, page: int) -> str:
        return f"{self.base_url}/chengjiao/pg{page}/"

    def _parse_listings(self, html: str, page_url: str) -> List[Dict]:
        soup = self.parse_html(html)
        items = soup.select("ul.sellListContent li.clear")
        if not items:
            self.logger.warning("No listings parsed from %s", page_url)
            return []

        rows: List[Dict] = []
        for li in items:
            title_tag = li.select_one("div.title a")
            title = title_tag.get_text(strip=True) if title_tag else ""
            detail_url = title_tag["href"] if title_tag and title_tag.has_attr("href") else page_url

            house_info_tag = li.select_one("div.houseInfo")
            house_info = house_info_tag.get_text(" ", strip=True) if house_info_tag else ""
            parts = [p.strip() for p in house_info.split("|")] if house_info else []

            house_type = parts[0] if len(parts) > 0 else ""
            area = self.to_float(parts[1]) if len(parts) > 1 else None
            orientation = parts[2] if len(parts) > 2 else ""
            decoration = parts[3] if len(parts) > 3 else ""
            floor = parts[4] if len(parts) > 4 else ""
            build_year = parts[5].replace("\u5e74\u5efa", "").strip() if len(parts) > 5 else ""

            community_tag = li.select_one("div.positionInfo a")
            community = community_tag.get_text(strip=True) if community_tag else ""
            region_tag = li.select_one("div.positionInfo a:nth-of-type(2)")
            region = region_tag.get_text(strip=True) if region_tag else ""

            total_price_tag = li.select_one("div.totalPrice span")
            total_price = self.to_float(total_price_tag.get_text() if total_price_tag else None)
            unit_price_tag = li.select_one("div.unitPrice span")
            unit_price = self.to_float(unit_price_tag.get_text() if unit_price_tag else None)

            rows.append(
                {
                    "source": "lianjia",
                    "city": self.city,
                    "region": region,
                    "community": community,
                    "title": title,
                    "house_type": house_type,
                    "area_sqm": area,
                    "orientation": orientation,
                    "decoration": decoration,
                    "floor": floor,
                    "build_year": build_year,
                    "total_price_wan": total_price,  # wan RMB
                    "unit_price": unit_price,       # yuan per sqm
                    "detail_url": detail_url,
                    "page_url": page_url,
                }
            )
        return rows

    def _parse_transactions(self, html: str, page_url: str) -> List[Dict]:
        soup = self.parse_html(html)
        items = soup.select("ul.listContent li")
        rows: List[Dict] = []
        for li in items:
            title_tag = li.select_one("div.title a")
            title = title_tag.get_text(strip=True) if title_tag else ""
            detail_url = title_tag["href"] if title_tag and title_tag.has_attr("href") else page_url

            deal_date_tag = li.select_one("div.dealDate")
            deal_date = deal_date_tag.get_text(strip=True) if deal_date_tag else ""

            deal_house_info_tag = li.select_one("div.houseInfo")
            deal_house_info = deal_house_info_tag.get_text(" ", strip=True) if deal_house_info_tag else ""

            unit_price_tag = li.select_one("div.unitPrice span")
            unit_price = self.to_float(unit_price_tag.get_text() if unit_price_tag else None)
            total_price_tag = li.select_one("div.totalPrice span")
            total_price = self.to_float(total_price_tag.get_text() if total_price_tag else None)

            position_tag = li.select_one("div.positionInfo")
            position = position_tag.get_text(" ", strip=True) if position_tag else ""

            rows.append(
                {
                    "source": "lianjia",
                    "city": self.city,
                    "title": title,
                    "deal_date": deal_date,
                    "house_info": deal_house_info,
                    "unit_price": unit_price,
                    "total_price_wan": total_price,
                    "position": position,
                    "detail_url": detail_url,
                    "page_url": page_url,
                }
            )

        if not rows:
            self.logger.warning("No transactions parsed from %s", page_url)
        return rows

    def crawl_listings(self) -> Iterator[Dict]:
        for page in range(1, self.pages + 1):
            url = self._listing_url(page)
            resp = self.get(url)
            if not resp:
                continue
            for row in self._parse_listings(resp.text, url):
                yield row
            self.random_delay()

    def crawl_transactions(self, pages: int = 1) -> Iterator[Dict]:
        for page in range(1, pages + 1):
            url = self._transaction_url(page)
            resp = self.get(url)
            if not resp:
                continue
            for row in self._parse_transactions(resp.text, url):
                yield row
            self.random_delay()

    def run(self) -> None:
        for row in self.crawl_listings():
            self.logger.info("Listing: %s | %s sqm | %s wan", row["title"], row["area_sqm"], row["total_price_wan"])
        for row in self.crawl_transactions(pages=1):
            self.logger.info("Deal: %s | %s | %s wan", row["title"], row["deal_date"], row["total_price_wan"])


if __name__ == "__main__":
    spider = LianjiaSpider(city="bj", region="haidian", pages=2, delay_range=(1, 2))
    spider.run()
