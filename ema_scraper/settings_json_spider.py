# Scrapy settings for ema_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from pathlib import Path
import logging
import os
BOT_NAME = "ema-json-spider"

SPIDER_MODULES = ["ema_scraper.spiders"]
NEWSPIDER_MODULE = "ema_scraper.spiders"

BASE_PATH = Path("~/Nextcloud/Datasets/ema_scraper").joinpath(BOT_NAME).expanduser()
os.makedirs(BASE_PATH, exist_ok=True)
    
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_PATH = BASE_PATH.joinpath("logs")
os.makedirs(LOG_PATH, exist_ok=True)
LOG_FILE_PATH = LOG_PATH.joinpath("crawl_json_spider.log")
LOG_FILE = str(LOG_FILE_PATH)
LOG_ENABLED = True
LOG_LEVEL = logging.INFO

# duplicate filtering
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'
DUPEFILTER_DEBUG = True  # Log filtered duplicates
                   
# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Personal Project (mdi@mailfence.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "ema_scraper.middlewares.EmaScrapySpiderMiddleware": 10,
}
DEPTH_LIMIT = 8
DEPTH_PRIORITY = 1

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "ema_scraper.middlewares.EmaScrapyDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# files pipeline with sitemap spider and http cache not required
ITEM_PIPELINES = {
    #"ema_scraper.pipelines.ItemPipeline:": 100,
    #"ema_scraper.pipelines.MongoPipeline": 200,
    "ema_scraper.pipelines.RedirectAwareFilesPipeline": 300,  
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 2
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = str(BASE_PATH.joinpath("cache").expanduser())
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Connection to MongoDB
MONGO_URI = "localhost:27017"
MONGO_DATABASE = "ema_scraper"

# Important: enable redirect handling
MEDIA_ALLOW_REDIRECTS = True
FILES_STORE = str(BASE_PATH.joinpath("files").expanduser())
FILES_URLS_FIELD = 'file_links'