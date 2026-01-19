
import pickle

from ema_scraper import settings
from utils.cache_utils import get_files_from_cache, get_pdfs_from_cache
import json

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")
PARSED_FILE_NAME = "parsed_pdf.pkl"
ema_json_all_docs = "medicines_output_documents_en.json"

with open(BASE_PATH.joinpath(ema_json_all_docs), "r") as f:
    all_docs_json = json.load(f)

parsed_files = get_files_from_cache(PARSED_FILE_NAME)
pdf_list, failed_pdfs = get_pdfs_from_cache()

'''
Loop over all scraped pdf and check which are available in the meta dict from ema
'''
all_docs_dict = {item["url"]: item for item in all_docs_json["data"]}
all_docs_url = [url for url in all_docs_dict.keys() if url.endswith(".pdf")]
all_scraped_docs_url = [item[1] for item in pdf_list]
items_no_info = []
for pdf_path, pdf_url in pdf_list:
    if pdf_url not in all_docs_dict:
        items_no_info.append(pdf_url)
        
n_total_ema_pdf = len([item for item in all_docs_dict.keys() if item.endswith('.pdf')])
print(f"Number of documents without meta info from ema: {len(items_no_info)}")
print(f"Total number of scraped pdf documents: {len(pdf_list)}")
print(f"Total number of ema docs according to ema meta info: {len(all_docs_dict)}")
print(
    f"Total number of ema pdf according to ema meta info: {n_total_ema_pdf}"
)
print(f"Missing number of pdfs (scraped-emainfo): {n_total_ema_pdf - len(pdf_list)}")

pdfs_not_scraped = set(all_docs_url) - set(all_scraped_docs_url)


n_docs = 100

docs = []
for i in range(0,n_docs):
    with open(df_entries[i], "rb") as f:
        docs.append(pickle.load(f))
        
no_title = []
for doc in docs:       
    item = json.loads(doc.json)
    if not item["metadata"]["title"]:
        no_title.append(doc.doc_id)