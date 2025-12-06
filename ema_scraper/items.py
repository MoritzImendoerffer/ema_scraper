# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

from enum import Enum

class LinkType(str, Enum):
    PAGE = "page"
    DOCUMENT = "document"
    EXTERNAL = "external"
    EXCLUDED = "excluded"

class DocType(str, Enum):
    GUIDELINE = "guideline"
    EPAR = "epar"
    COMMITTEE_PAGE = "committee_page"
    UNKNOWN = "unknown"


class PageItem(scrapy.Item):
    """A crawled HTML page."""
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    html_raw = scrapy.Field()
    doc_type = scrapy.Field()          # DocType enum value
    ema_tags = scrapy.Field()          # list[str]
    metadata = scrapy.Field()          # dict
    crawled_at = scrapy.Field()        # datetime


class DocumentItem(scrapy.Item):
    """A discovered document (PDF, Excel, etc.) - not yet downloaded."""
    url = scrapy.Field()
    parent_page_url = scrapy.Field()
    filename = scrapy.Field()
    doc_type = scrapy.Field()
    download_status = scrapy.Field()   # pending | downloaded | failed
    discovered_at = scrapy.Field()


class LinkItem(scrapy.Item):
    """A relationship between two URLs."""
    source_url = scrapy.Field()
    target_url = scrapy.Field()
    link_type = scrapy.Field()         # LinkType enum value
    anchor_text = scrapy.Field()
    context = scrapy.Field()           # surrounding sentence