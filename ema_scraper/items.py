# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from urllib.parse import urlparse
from enum import Enum
from config_loader import load_config
import regex as re
import pathlib

config = load_config(pathlib.Path("config.yml"))


class LinkType(str, Enum):
    PAGE = "page"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_url(cls, url: str) -> "LinkType":
        """Infer LinkType from URL path. 
        Not sure if this function is required.
        """
        url_parsed = urlparse(url)
        if any([re.findall(item, url_parsed.path) for item in config["scraper"]["file_patterns"]]):
            return cls.DOCUMENT
        if any([re.findall(item, url_parsed.path) for item in config["scraper"]["image_patterns"]]):
            return cls.IMAGE
        if any([re.findall(item, url_parsed.path) for item in config["scraper"]["video_patterns"]]):
            return cls.VIDEO
        if any([re.findall(item, url_parsed.path) for item in config["scraper"]["audio_patterns"]]):
            return cls.AUDIO                
        if (url_parsed.path.endswith(".html")) | (url_parsed.path.endswith(".htm")):
            return cls.PAGE
        
        return cls.UNKNOWN

class DocType(str, Enum):
    GUIDELINE = "guideline"
    EPAR = "epar"
    COMMITTEE_PAGE = "committee_page"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_url(cls, url: str) -> "DocType":
        """Infer DocType from URL path."""
        path = urlparse(url).path.lower()
        
        patterns = {
            cls.EPAR: ["/epar/", "/medicines/human/epar"],
            cls.GUIDELINE: ["/guideline", "/scientific-guidelines"],
            cls.COMMITTEE_PAGE: ["/committee"],
        }
        
        for doc_type, keywords in patterns.items():
            if any(kw in path for kw in keywords):
                return doc_type
        
        return cls.UNKNOWN

class PageItem(scrapy.Item):
    """A crawled HTML page."""
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    html_raw = scrapy.Field()
    ema_tags = scrapy.Field()  # list[str]
    metadata = scrapy.Field()  # dict
    crawled_at = scrapy.Field()  # datetime

class DocItem(scrapy.Item):
    """A crawled HTML page."""
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    byteraw = scrapy.Field()
    doc_type = scrapy.Field()

class DocumentItem(scrapy.Item):
    """A document linked within a scraped page (PDF, Excel, etc.)"""
    url = scrapy.Field()
    doc_type = scrapy.Field()  # DocType enum value
    parent_page_url = scrapy.Field()
    filename = scrapy.Field()
    download_status = scrapy.Field()  # pending | downloaded | failed
    ema_tags = scrapy.Field()  # list[str]
    metadata = scrapy.Field()  # dict
    downloaded_at = scrapy.Field()  # datetime

class LinkItem(scrapy.Item):
    """A relationship between two URLs."""
    source_url = scrapy.Field()
    target_url = scrapy.Field()
    link_type = scrapy.Field()  # LinkType enum value
    anchor_text = scrapy.Field()
    context = scrapy.Field()  # surrounding sentence of link
    
if __name__ == "__main__":
    print("debugging")