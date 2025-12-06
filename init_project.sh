conda create -n scrapy -f requirements.yml
conda activate scrapy
scrapy startproject ema_scrapy

mkdir -p storage

# flatten the folder structure and use run_spider.py as entrypoint
cd ema_scrapy && mv ema_scrapy/* . && rmdir ema_scrapy

