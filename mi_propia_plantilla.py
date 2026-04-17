import scrapy
from scrapy.crawler import CrawlerProcess
from openpyxl import Workbook
from tqdm import tqdm
import os

LIMITE = 100

class ExcelPipeline:
    def open_spider(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["TITULAR", "LINK", "FECHA", "CUERPO DE LA NOTICIA"])
        self.barra = tqdm(total=LIMITE, desc="Noticias", unit="noticia",
                          bar_format="{l_bar}{bar:30}{r_bar}")

    def process_item(self, item):
        self.ws.append([
            item.get("titular"),
            item.get("link"),
            item.get("fecha"),
            item.get("cuerpo"),
        ])
        self.barra.update(1)
        return item

    def close_spider(self):
        self.barra.close()
        self.wb.save(os.path.abspath("Spider_Pachamama.xlsx"))
        print(f"\n✅ Archivo guardado con {self.ws.max_row - 1} noticias")


class HuilaSpider(scrapy.Spider):
    name = "noticias"

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'ITEM_PIPELINES': {
            '__main__.ExcelPipeline': 300,
        }
    }

    start_urls = [
        'https://pachamamaradio.org/',
        'https://pachamamaradio.org/puno/',
        'https://pachamamaradio.org/nacional/',
        'https://pachamamaradio.org/actualidad/',
        'https://pachamamaradio.org/internacional/'

    ]

    def parse(self, response):
        for link in response.css("h3.entry-title.td-module-title > a::attr(href)").getall():
            yield response.follow(link, callback=self.parse_noticias)

    def parse_noticias(self, response):
        yield {
            "titular": response.css("h1.tdb-title-text::text").get(),
            "link": response.url,
            "fecha": response.css("time.entry-date.updated.td-module-date::attr(datetime)").get()[:10],
            "cuerpo": " ".join(response.css("div.tdb-block-inner.td-fix-index > p::text").getall()).strip()
        }


process = CrawlerProcess(settings={
    "LOG_LEVEL": "INFO",
    "CONCURRENT_REQUESTS": 8,
    "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    "DOWNLOAD_TIMEOUT": 30,
    "RETRY_TIMES": 3,
    "DOWNLOAD_DELAY": 0.5,
    "COOKIES_ENABLED": False,
    "CLOSESPIDER_ITEMCOUNT": LIMITE,
})
process.crawl(HuilaSpider)
process.start()
