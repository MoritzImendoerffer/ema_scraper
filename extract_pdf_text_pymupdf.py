from ema_scraper import settings
from multiprocessing import Pool, cpu_count, get_context
from tqdm import tqdm
from parsers import PyMuPdfParser
import pickle
import logging
from utils.cache_utils import get_pdfs_from_cache, get_files_from_cache
import argparse
"""
This script uses the cached pdf responses and extracts json as well as markdown 
and saves a pickled document item in the cache folder with name PARSED_FILE_NAME.

Currently, scraping and text extraction from pdfs is separated. PDF parsing is hard and probably iterative.
Parsing pdfs from cache is the faster option at the moment.
"""

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")
OVERWRITE = False
PARSED_FILE_NAME = "parsed_pdf.pkl"
SPLIT_FILE = BASE_PATH.joinpath("follower_entries.pkl")

_parser = PyMuPdfParser()

def init_worker():
    import logging
    global _parser
    logging.basicConfig(
        level=logging.WARNING,
        format='%(processName)s - %(message)s',
        filename=BASE_PATH.joinpath('pdf_extraction.log'),
        filemode='a'
    )
    
def extract_pdf(args):
    logger = logging.getLogger(__name__)  # Get logger inside function
    root, url = args
    try:
        if root.joinpath(PARSED_FILE_NAME).exists() and not OVERWRITE:
            return
        with open(root.joinpath("response_body"), "rb") as r:
            response = r.read()
        doc = _parser.parse(response, doc_id=url)
        temp_path = root.joinpath(f"{PARSED_FILE_NAME}.tmp")
        with open(temp_path, "wb") as pd:
            pickle.dump(doc, pd)
        temp_path.rename(root.joinpath(PARSED_FILE_NAME))
    except Exception as e:
        logger.warning(f"Could not parse {root} \n {e}")


if __name__ == "__main__":
    if SPLIT_FILE.exists():
        # Follower: load assigned work
        with open(SPLIT_FILE, "rb") as f:
            my_entries = pickle.load(f)
        print(f"Follower mode: processing {len(my_entries)} entries")
    else:
        # Leader: create the split
        pdf_entries, failed_pdfs = get_pdfs_from_cache()
        pdf_folders = [item[0] for item in pdf_entries]
        processed_pdfs = get_files_from_cache("parsed_pdf.pkl")
        processed_pdf_folders = [item.parent for item in processed_pdfs]
        to_process = set(pdf_folders) - set(processed_pdf_folders)
        pdf_entries_to_process = [item for item in pdf_entries if item[0] in to_process]
        assert len(pdf_entries_to_process) + len(processed_pdfs) - len(pdf_entries) == 0
        
        midpoint = len(pdf_entries_to_process) // 2
        my_entries = pdf_entries_to_process[:midpoint]
        follower_entries = pdf_entries_to_process[midpoint:]
        
        with open(SPLIT_FILE, "wb") as f:
            pickle.dump(follower_entries, f)
        
        print(f"Leader mode: processing {len(my_entries)}, saved {len(follower_entries)} for follower")
    
    # Parallel extraction
    with get_context("spawn").Pool(cpu_count(), initializer=init_worker) as pool:
        list(tqdm(pool.imap(extract_pdf, my_entries, chunksize=10), 
                  total=len(my_entries), 
                  desc="Parsing PDFs"))