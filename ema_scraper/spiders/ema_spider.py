import scrapy
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import regex as re
import logging
logger = logging.getHandlerByName("ema_scraper")

class EmaSpider(CrawlSpider):
    name = "ema"
    pass