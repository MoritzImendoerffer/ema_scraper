from ema_scraper.spiders.ema_spider import EmaSpider
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from ema_scraper import settings as my_settings
from config_loader import load_config
import logging
import pathlib

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="crawl.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
"""
Entry point to run spider. Better for debugging.
Requires the flat folder structure enfored in init_project.sh
"""

crawler_settings = Settings()
crawler_settings.setmodule(my_settings)
process = CrawlerProcess(settings=crawler_settings)
process.crawl(EmaSpider)
process.start()