import glob
from ema_scraper import settings
import ast
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from parsers.pdf_parser import DocumentStyleExtractor
from sklearn.feature_extraction.text import CountVectorizer
import pickle

"""
This script uses the cached pdf responses and extracts formatting styles from the pdfs.

Currently, scraping and text extraction from pdfs is separated. PDF parsing is hard and probably iterative.
Parsing pdfs from cache is the faster option at the moment.

This script saves the extracted entries (path, meta) using DocumentStyleExtractor into the base directory of the cache
with filename FILE_NAME.
"""


from utils.cache_utils import get_files_from_cache, get_pdfs_from_cache

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")
FILE_NAME = "pdf_profile.pickle"
# Worker function (must be at module level for pickling)
def extract_pdf(args):
    root, url = args
    extractor = DocumentStyleExtractor()
    try:
        with open(root.joinpath("response_body"), "rb") as r:
            response = r.read()
        profile = extractor.extract(response, doc_id=url)
        return (root, profile)
    except Exception as e:
        return (root, None)

def get_pdf_meta():
    # First pass: collect PDF entries
    pdf_entries, failed = get_pdfs_from_cache()

    # Second pass: parallel extraction
    results = []
    with Pool(cpu_count()) as pool:
        for result in tqdm(pool.imap(extract_pdf, pdf_entries), total=len(pdf_entries), desc="Extracting styles"):
            results.append(result)
    return results

if __name__ == "__main__":
    # Filter out failures
    results = get_pdf_meta()
    results = [(root, profile) for root, profile in results if profile is not None]
    with open(BASE_PATH.joinpath(FILE_NAME), "wb") as f:
        pickle.dump(results, f)
        
