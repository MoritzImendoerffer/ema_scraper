import pathlib
import scrapy
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, SitemapSpider, Request
from ema_scraper.items import PageItem, PageItemSimple
import regex as re
import logging
from config_loader import load_config
from scrapy.link import Link
from urllib.parse import urlparse

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

class EmaSitemapSpider(SitemapSpider):
    """
    This might be simpler compared to my CrawlSpider approach. A learning and TODO for a future version.
    """
    name = "ema-sitemap"
    sitemap_urls = ["https://www.ema.europa.eu/sitemap.xml"]
    allowed_domains = scraper_config.get("allowed_domains", list())
    sitemap_rules = [
    (r'/en/', 'parse')]
    
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
        r".*\.ZIP",
        r".*/EN/TXT/PDF/.*"  # include eur-lex.europa.eu items if PDF
    ]
        
    async def start(self):
        async for item_or_request in super().start():
            yield item_or_request
            
    def get_content_type(self, response):
            try:
                return str(response.headers.to_unicode_dict()['Content-Type']).split(';')[0]
            except AttributeError:
                pass
            except KeyError:
                return None
            return None
        
    def parse(self, response):
        url = response.url
        logger.info(f"Crawled page {response.url}")
        content_type = self.get_content_type(response)
        loader = ItemLoader(item=PageItemSimple(), response=response)
        
            
        loader.add_value('url', response.url)
        loader.add_value('content_type', content_type)
        if content_type == "text/html":
            loader.add_value("html_raw", response.text) 
        else:
            for search_pattern in self.regex_file_patterns:
                if re.findall(search_pattern, url):
                    loader.add_value("file_links", response.url)
        # else:
        #     for search_pattern in self.regex_file_patterns:
        #         if re.findall(search_pattern, url):
        #             loader.add_value('file_links', url)
        yield loader.load_item()
        
class EmaSpider(CrawlSpider):
    name = "ema"
    allowed_domains = []  # populated from config
    start_urls = []
    
    # TODO: use config from config.yml
    # used to detect file links which are stored in the item (LinkExtractor is using them)
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
    
    
    exluded_sections = ["Topics",
                        "Contact"]

    allowed_domains = scraper_config.get("allowed_domains", list())
    start_urls = scraper_config.get("start_urls", list())
    max_nodes = scraper_config.get("max_nodes", 100)

    parser_map = {
        "/en/medicines/human/EPAR": "parse_with_sidebar",
        "/en/human-regulatory-overview": "parse_with_sidebar",
    }
    
    def get_parser_for_url(self, url):
        """Find parser by longest matching prefix, fallback to parse_default
        A possible improvement for the future:
        Use a parser factory pattern to separate the parsing and parser selection part from the Spider.
        """
        match_dict = {}
        for key in self.parser_map.keys():
            upath = urlparse(url).path.strip("/").split("/")
            rpath = key.strip("/").split("/")
            n_match = 0
            for match_item in zip(upath, rpath):
                if match_item[0] == match_item[1]:
                    n_match += 1
                else:
                    break
            
            match_dict[key] = n_match
        
        # Filter to only patterns with at least 1 match
        valid_matches = {k: v for k, v in match_dict.items() if v > 0}
        
        if valid_matches:
            # Handle ties: use longest key as tiebreaker
            parser_key = max(valid_matches.keys(), 
                            key=lambda k: (valid_matches[k], len(k)))
            parser_name = self.parser_map[parser_key]
        else:
            logger.warning(f"No valid matches found using default parser: {url}")
            parser_name = "parse_default"
        
        parser_method = getattr(self, parser_name, None)
        if parser_method is None:
            logger.warning(f"Parser method '{parser_name}' not found! Using parse_default")
            parser_method = self.parse_default
            
        logger.info(f"Parsing {url} with {parser_method.__name__}")
        
        return parser_method
    
    def parse(self, response):
        parser = self.get_parser_for_url(response.url)
        return parser(response)

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
    
    def parse_default(self, response):
        return self.parse_with_sidebar(response)
    
    def parse_human_epar(self, response):
        """ Parser for EPAR sites like:
        https://www.ema.europa.eu/en/medicines/human/EPAR
        
        https://www.ema.europa.eu/en/medicines/human/EPAR/avastin
        """
        raise NotImplementedError
    
    
    def parse_with_sidebar(self, response):
        """ Standard parser for sites like
        https://www.ema.europa.eu/en/human-regulatory-overview/research-development/quality-design
        """
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
                if not section_ids:
                    logger.warning(f"No section ids found for {response.url}")
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
                
                # exclude unwanted pattern in links
                excluded_page_links = []
                for search_pattern in config["scraper"]["exclude_patterns"]:
                    for _link in flat_links:
                        if re.findall(search_pattern, _link):
                            excluded_page_links.append(_link)
                
                loader.add_value("file_links", file_links)
                
                # follow all links in the page
                page_links = list(set(flat_links) - set(file_links) - set(excluded_page_links))
                loader.add_value("page_links", page_links)
                
                # TODO check if I need a Link object to follow
                
                for pl in page_links:
                    try:
                        logger.info(f"Following page link (source, target): {(response.url, pl)})")
                        yield response.follow(pl, self.parse, meta={"source_url": response.url})
                    except Exception as e:
                        logger.warning(f"Could not follow: {pl} with error {e}")
                
                logger.info(f"Yielded item: {response.url}")
                yield loader.load_item()

            else:
                # the item slipped through the hardcoded link detection, treat as regular item
                # filtering is done during post processing. Harcoded link detection does save time due to less requests, however, post processing is less lean.
                assert response.meta["source_url"]
                loader.add_value("file_links", response.url)
                yield loader.load_item()

        except Exception as e:
            logging.warning(f"Exception during parsing for {response.url} with error {e}")
        

    