# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
#from itemadapter import ItemAdapter
from scrapy.pipelines.files import FilesPipeline
import pymongo
class EmaScrapyPipeline:
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
            mongo_db=crawler.settings.get("MONGO_DATABASE", "items"),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        sitem = {}
        resp = item["response"][0]
        resp.request.callback = None
        sitem["response"] = {}
        keys_to_add = [key for key in item.keys() if key != 'response']
        for key in keys_to_add:
            sitem[key] = item[key]
            
        resp_keys_to_add = resp.attributes
        att2add = ["url", "headers", "body", "request"]
        for att in att2add:
            if att not in resp_keys_to_add:
                resp_keys_to_add.append(att)
        for att in resp_keys_to_add:
            if att in att2add:
                sitem["response"][att] = eval(f"resp.{att}")
            else:
                sitem["response"][att] = None
                
        #TODO check if example with Itemsadaper might save me of using the hardcoded
        # logic in process_item
        # source https://docs.scrapy.org/en/latest/topics/item-pipeline.html
        #self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        self.db[self.collection_name].insert_one(sitem)
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