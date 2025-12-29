# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
#from itemadapter import ItemAdapter
from scrapy.pipelines.files import FilesPipeline
from pymongo.errors import DuplicateKeyError
from scrapy.exceptions import DropItem
import pymongo
import json
import logging
logger = logging.getLogger(__name__)

class ItemPipeline:
    def process_item(self, item, spider):
        return item

        
class MongoPipeline:
    collection_name = "web_items" # TODO: how to move to settings?

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", cls.collection_name),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db[self.collection_name].create_index("url", unique=True)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            self.db[self.collection_name].insert_one({key: value for key, value in item.items()})
        except Exception as e:
            logger.warning(f"Saving to MongoDB failed: {e}")
        return item



class RedirectAwareFilesPipeline(FilesPipeline):
    """
    Custom FilesPipeline that captures redirect information.

    This allows matching discovered URLs (from HTML crawling) with canonical URLs
    (from EMA JSON indices) even when redirects occur.

    Result dict per file will contain:
    - url: originally requested URL (discovered from HTML)
    - final_url: URL after all redirects (canonical, matches JSON)
    - redirect_chain: list of intermediate redirect URLs
    - path: local storage path
    - checksum: MD5 hash
    - status: download status
    """


    def media_downloaded(self, response, request, info, *, item=None):
        """
        Override to add redirect information to the result dict.
        """
        # Get the standard result from parent
        result = super().media_downloaded(response, request, info, item=item)
        
        # Add redirect information
        # response.url is the final URL after all redirects
        # request.url is the originally requested URL (already in result['url'])
        result['final_url'] = response.url
        
        # redirect_urls contains the chain of redirects (if any)
        # Empty list if no redirects occurred
        result['redirect_chain'] = response.meta.get('redirect_urls', [])
        
        return result