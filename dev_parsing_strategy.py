from pymongo import MongoClient
from markdownify import markdownify as md
from html_to_markdown import convert
import pypandoc

from ema_scraper import settings as my_settings
from parsers.ema_parser import parse_ema_page, ema_to_markdown
from utils.mongo_utils import connect

import json

"""
# Aim
Test differnt parsing strategies. Markdownify versus elaborate parser based on components defined in

https://ec.europa.eu/component-library/ec/components/
https://github.com/openeuropa

"""
url = "https://www.ema.europa.eu/en/human-regulatory-overview/research-development/innovation-task-force-briefing-meetings"

mc = connect()

item = list(mc.find({"url": url}))[0]
html = item["html_raw"][0]
markdown = md(html)
markdown_html2 = convert(html)
pan = pypandoc.convert_text(html, to="markdown", format="html")
pars_json = parse_ema_page(html)
ema_md = ema_to_markdown(html)

with open(my_settings.BASE_PATH.joinpath("markdown_all_markdownify.md").expanduser(), "w") as f:
    f.write(markdown)
    
with open(my_settings.BASE_PATH.joinpath("markdown_all_html2.md").expanduser(), "w") as f:
    f.write(markdown_html2)
    
with open(my_settings.BASE_PATH.joinpath("markdown_all_pandoc.md").expanduser(), "w") as f:
    f.write(pan)

with open(my_settings.BASE_PATH.joinpath("json_all_emaparser.json").expanduser(), "w") as f:
    json.dump(pars_json, f)
    
with open(my_settings.BASE_PATH.joinpath("markdown_all_emaparser.md").expanduser(), "w") as f:
    f.write(ema_md)
    
    
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')
faq_heading = soup.find('h2', string=lambda s: s and 'Frequently asked questions' in s)
if faq_heading:
    # Get parent and siblings
    parent = faq_heading.parent
    print(parent.prettify()[:3000])