from ema_scrapy.spiders.ema_spider import EmaSpider
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from ema_scrapy import settings as my_settings


from logger_helper import get_logger
logger = get_logger(name="ema_scraper", log_file="ema_scraper.log")
"""
Entry point to run spider. Better for debugging.
Requires the flat folder structure enfored in init_project.sh
"""

crawler_settings = Settings()
crawler_settings.setmodule(my_settings)
process = CrawlerProcess(settings=crawler_settings)
process.crawl(EmaSpider)
process.start()