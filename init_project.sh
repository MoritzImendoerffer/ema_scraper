conda create -n scrapy -f requirements.yml
conda activate scrapy
scrapy startproject ema_scraper

mkdir -p storage

# flatten the folder structure and use run_spider.py as entrypoint
cd ema_scraper && mv ema_scraper/* . && rmdir ema_scraper

# TODO: add startup for mongoDB

