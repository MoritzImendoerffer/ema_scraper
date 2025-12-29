from ema_scraper.spiders.ema_spider import EmaJsonSpider
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from ema_scraper import settings_json_spider as my_settings
from scrapy.utils.log import configure_logging


"""
Entry point to run the json spider spider. Better for debugging.
Requires the flat folder structure enfored in init_project.sh
"""

crawler_settings = Settings()
crawler_settings.setmodule(my_settings)
configure_logging(crawler_settings)
process = CrawlerProcess(settings=crawler_settings, install_root_handler=True)

process.crawl(EmaJsonSpider)
process.start()