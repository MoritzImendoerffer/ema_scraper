"""
TODO:

- [ ] Parse 
"""
import regex as re
from ema_scraper import settings as my_settings

site_map_urls = my_settings.LOG_PATH.joinpath("sitemap_urls").joinpath("sitemap_urls.txt")
urls = []
with open(site_map_urls, "r") as f:
    for line in f:
        urls.append(line.strip("\n"))

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
    r".*\.png",
    r".*.[A-Za-z]{3,4}$",
    r".*/EN/TXT/PDF/.*"  # include eur-lex.europa.eu items if PDF
]


urls_no_files = []
for url in urls:
    found = False
    for pattern in regex_file_patterns:
        if re.match(pattern, url):
            found = True
    if not found:
        urls_no_files.append(url)

level_1_set = set()
for url in urls_no_files:
    level_1_set.add(url.split("//")[1].split("/")[2])

with open(my_settings.LOG_PATH.joinpath("sitemap_urls").joinpath("web-pages"), "w") as f:
    for url in urls_no_files:
        f.write(url + "\n")