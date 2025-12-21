# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class PageItemSimple(scrapy.Item):
    url = scrapy.Field()
    html_raw = scrapy.Field()
    file_links = scrapy.Field()
    content_type = scrapy.Field()
    
class PageItem(scrapy.Item):
    """A crawled HTML page."""
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    html_raw = scrapy.Field()
    ema_category = scrapy.Field()  # list[str]
    ema_topic = scrapy.Field()
    metadata = scrapy.Field()  # dict
    crawled_at = scrapy.Field()  # datetime
    content_type = scrapy.Field() # content type from html header
    sections = scrapy.Field()
    summary = scrapy.Field()
    file_links = scrapy.Field()
    page_links = scrapy.Field()
    source_url = scrapy.Field()
