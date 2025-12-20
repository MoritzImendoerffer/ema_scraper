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
from scrapy.link import Link

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
    
    rules = (
        Rule(LinkExtractor(allow=r'/'), callback='parse', follow=True),
    )
    
    exluded_sections = ["Topics"]

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
                
                cat_labels = []
                try:
                    cat_labels = [item.css("::text").get() for item in response.css(".ema-bg-category")]
                except Exception as e:
                    logger.warning(f"Error in category label extraction for {response.url} with error {e}")
                loader.add_value("ema_category", cat_labels)
                
                topic_labels = []
                try:
                    topic_labels = [item.css("::text").get() for item in response.css(".ema-bg-topic")]
                except Exception as e:
                    logger.warning(f"Error in topic label extraction for {response.url} with error {e}")
                loader.add_value("ema_topic", topic_labels)
                   
                #main_content = response.css(".ema-node-content-wrapper")
                main_items = response.css(".ema-node-content-wrapper > .item")

                
                '''
                Loop over the section from the sidebar, extract the page content and parse links and text for each section if not exluded.
                
                '''
                # usually there is a summary on top of the sections
                # this part will not be reached by the sidebar nav items and contains a short summary
                try:
                    summary = " ".join([item.strip() for item in main_items[0].css("::text").getall()]).replace("  ", " ").strip()
                except Exception as e:
                    summary = ""
                    logger.warning(f"Summary strategy does not work for {response.url} with error: {e}")
                loader.add_value("summary", summary)
                
                # the individual sections defined in the sidebar
                section_ids = [item.css("::attr(href)").get() for item in response.css(".bcl-inpage-navigation").css(".nav-item")]
                all_links = []
                page_links = []
                file_links = []
                section_titles = []
                section_text = []
                for id in section_ids:
                    # get the parent item for each section which wraps all links and text
                    section = response.xpath(f'//div[@id="{id[1:]}"]//ancestor::div[@class="item"]')
                    heading = section.css("h2::text").get()
                    if heading not in self.exluded_sections:
                        section_titles.append(heading)
                        text = section.css("p::text").getall()
                        section_text.append(text)
                        links = section.css("::attr(href)").getall()
                        if links:
                            all_links.append([response.urljoin(item) for item in links])
                
                section_info = {tit: {"text": tex, "links": lin} for tit, tex, lin in zip(section_titles, section_text, all_links)}
                loader.add_value("sections", section_info)
                
                
                # get the files to download using scrapys FileDownloader
                flat_links = [subitem for item in all_links for subitem in item]
                for search_pattern in self.regex_file_patterns:
                    for _link in flat_links:
                        if re.findall(search_pattern, _link):
                            file_links.append(_link)
                            
                loader.add_value("file_links", file_links)

                
                # follow all links in the page
                page_links = list(set(flat_links) - set(file_links))
                loader.add_value("page_links", page_links)
                
                # TODO check if I need a Link object to follow
                
                for pl in page_links:
                    try:
                        yield response.follow(pl, self.parse, meta={"source_url": response.url})
                    except Exception as e:
                        logger.warning(f"Could not follow: {pl} with error {e}")
                
                yield loader.load_item()

            else:
                # the item slipped through the hardcoded link detection, treat as regular item
                # filtering is done during post processing. Harcoded link detection does save time due to less requests, however, post processing is less lean.
                assert response.meta["source_url"]
                loader.add_value("file_links", response.url)
                yield loader.load_item()

        except Exception as e:
            logging.warning(f"Exception during parsing for {response.url} with error {e}")
        

    