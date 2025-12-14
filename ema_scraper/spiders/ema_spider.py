import pathlib
import scrapy
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ema_scraper.items import LinkItem, PageItem
from ema_scraper.items import LinkType, DocType
import regex as re
import logging
from config_loader import load_config

"""
Scraper for ema.europa.eu

Strategy:

1) Scrape all html pages into mongodb
2) Use links between pages to establish a neo4j graph as basis for agentic graph based rag
3) Use scrapys file downloader to get all english pdfs which are linked in the files
4) Use the json from ema to get the metadata for each file
5) Files should be also nodes that means each file has a mongodb entry with metadata and link to the file
6) PDFs should be parsed but for now just focus on html
8) Treat external content (e.g. Eudralex) as node but it remains a stump for now. Parsing eudralex is a focus for later.
9) Is it better to parse the html logic while scraping, or scrape raw html into mongoDB and later use e.g Beautiful soup with the mongoDB
   I do have more flexibility. E.g. there is an item called <article class=content-with-sidebar node ema-general--full ...
   How many different articles are there? Which sections to scrape? E.g. Topics leads to a search page for a database but I do have the json info
   from https://www.ema.europa.eu/en/about-us/about-website/download-website-data-json-data-format
   
Use https://pypi.org/project/eurlex-parser/ for parsing eudralex parsing
"""

logger = logging.getLogger(__name__)

config = load_config(pathlib.Path("config.yml"))
scraper_config = config["scraper"]

def html_parser(response):
    print("parsed html")
    
def unknown_parser(response):
    logger.warning(f"Content type not implemented: {str(response.headers.to_unicode_dict()['Content-Type']).split(';')[0]}")
    return None    

registered_parser = {
    "text/html": html_parser
}
class EmaSpider(CrawlSpider):
    name = "ema"
    allowed_domains = []
    start_urls = []
    max_nodes = 200
    visited_count = 0

    # TODO: add option to steer via settings or other means
    regex_file_patterns = [
        r"^https?://eur-lex\.europa\.eu/.*\?uri=.*:PDF$",
        r".*\.pdf",
        r".*\.PDF",
        r".*\.xlsx",
        r".*\.XLSX",
        r".*\.xls",
        r".*\.XLS",
        r".*\.docx",
        r".*\.DOCX",
        r".*\.doc",
        r".*\.DOC",
        r".*\.pptx",
        r".*\.PPTX",
        r".*\.ppt",
        r".*\.PPT",
        r".*\.zip",
        r".*\.ZIP"
        r".*/EN/TXT/PDF/.*"  # include eur-lex.europa.eu items if PDF
    ]

    regex_exclude_patterns = [
        r"^mailto:.*",
        r".*\.svg",
        r".*\.png",
        r".*\.jpeg",
        r".*\.jpg",
        r".*\.xml",
        r".*\.xsd",
        r".*javascript:.*",
        r"^tel:.*",
        r"^https://www.ema.europa.eu.*/documents/*/.*_(?!en)[a-z]{2}-\d{1,2}.pdf",  # same but for all documents with version numbers
        r"^https://www.ema.europa.eu.*/documents/*/.*_(?!en)[a-z]{2}.pdf",  # exclude all non english pdfs from ema
        r".*\/(?!EN)[A-Z]{2}\/TXT\/.*", # for the eur-lex.europa.eu items, exclude all non english versions
        r"^https://eur-lex.europa.eu/legal-content/(?!EN)[A-Z]{2}/ALL" # for the eur-lex.europa.eu items, exclude all non english versions
    ]
    regex_modify_links_to_filelinks = [
        (r"(https://eur-lex\.europa\.eu/legal-content/EN/)ALL", r"\1TXT/HTML", # only download the english html version. Ignore all other links
         r"(https://ema.europa.eu):\d{3}", r"\1")  # replace port number 443 in url

    ]    
    
    link_extractor = LinkExtractor()
    rules = (
        Rule(LinkExtractor(allow=r'/'), callback='parse', follow=True),
    )

    allowed_domains = scraper_config.get("allowed_domains", list())
    start_urls = scraper_config.get("start_urls", list())
    max_nodes = scraper_config.get("max_nodes", 100)


    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)       

    def get_content_type(self, response):
        try:
            return str(response.headers.to_unicode_dict()['Content-Type']).split(';')[0]
        except AttributeError:
            pass
        except KeyError:
            return None
        return None
    
    def _parse_main_body(self, response):
        
        return 0 

    def parse(self, response):
        self.visited_count += 1
        
        if self.visited_count > self.max_nodes:
            logger.info("Reached count max_nodes. Stopping")
            return
        
        # main content is in class region-content
        content_type = self.get_content_type(response)
        loader = ItemLoader(item=PageItem(), response=response)
        loader.add_value('url', response.url)
        loader.add_value("html_raw", response.text) 
        loader.add_value('content_type', content_type)
        if "source_url" in response.meta.keys():
            loader.add_value("source_url", response.meta["source_url"])

        try:
            if content_type == "text/html":
                
                # TODO: parse sections of the main body
                # get heading-title in main-content
                # get labels from items with class containing "ema-bg-category badge" and "ema-bg-topic badge" for meta tags
                # get text from class "region-conten-main row"
                # TODO: there is a class called <article class=content-with-sidebar node ema-general--full ...
                # how many article types are there? Is it possible to extract all article types from the ema page? 
                # Or should I go one by one and add new parsing strategies once new articles there are?
                # Probably raw html in mongoDB and while looping over mongo nodes and then decide on parsing strategy!!
                # TODO: think about integrating json file information
                

                all_links = self.link_extractor.link_extractor.extract_links(response)
                all_link_urls = [item.url for item in all_links]
                page_links = all_link_urls

                # get the files to download using scrapys FileDownloader
                # TODO: check if still relevant or if a simpler method is possible
                # e.g. by simply using the main body of the page
                file_links = []
                for search_pattern in self.regex_file_patterns:
                    for _link in page_links:
                        if re.findall(search_pattern, _link):
                            file_links.append(_link)

                page_links = list(set(page_links) - set(file_links))

                exclude_file_links = []
                for search_pattern in self.regex_exclude_patterns:
                    for _link in file_links:
                        if re.findall(search_pattern, _link):
                            exclude_file_links.append(_link)

                file_links = list(set(file_links) - set(exclude_file_links))
                
                if file_links:
                    for _f in file_links:
                        if _f.endswith("_sk.pdf"):
                            print(_f)
                    loader.add_value("file_links", file_links)

                # follow all links in the page
                
                loader.add_value("page_links", page_links)
                
                for pl in page_links:
                    try:
                        yield response.follow(pl, self.parse, meta={"source_url": response.url})
                    except Exception as e:
                        with open('failed_requests.txt', 'a') as f:
                            f.write(pl + ":" + " " + str(e) + "\n")
                
                yield loader.load_item()

            else:
                # the item slipped through the hardcoded link detection, treat as regular item
                # filtering is done during post processing. Harcoded link detection does save time due to less requests, however, post processing is less lean.
                assert response.meta["source_url"]
                loader.add_value("file_links", response.url)
                yield loader.load_item()

        except Exception as e:
            logging.info(str(response.url) + ":" + " " + str(e))
        

    