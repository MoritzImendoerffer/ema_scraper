from ema_scraper.spiders.ema_spider import EmaSpider, EmaSitemapSpider, EmaSitemapExtractor
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from ema_scraper import settings as my_settings
from scrapy.utils.log import configure_logging
from config_loader import load_config
import logging
import pathlib


"""
Entry point to run spider. Better for debugging.
Requires the flat folder structure enfored in init_project.sh
"""

crawler_settings = Settings()
crawler_settings.setmodule(my_settings)
configure_logging(crawler_settings)
process = CrawlerProcess(settings=crawler_settings, install_root_handler=True)

# logging.basicConfig(
#     filename="crawl.log", 
#     format= "%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
#     level=logging.INFO
# )
#process.crawl(EmaSpider)
process.crawl(EmaSitemapSpider)
#process.crawl(EmaSitemapExtractor, settings={'LOG_FILE': str(my_settings.LOG_PATH.joinpath("xml_spider.log"))})
process.start()