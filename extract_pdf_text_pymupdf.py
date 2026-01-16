import glob
from ema_scraper import settings
import ast
from multiprocessing import Pool, cpu_count, get_context
from tqdm import tqdm
from parsers.pdf_parser import PyMuPdfParser
import pickle
import logging


BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")
OVERWRITE = False
PARSED_FILE_NAME = "parsed_pdf.pkl"

def init_worker():
    import logging
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
        extractor = PyMuPdfParser()
        with open(root.joinpath("response_body"), "rb") as r:
            response = r.read()
        doc = extractor.parse(response, doc_id=url, save_doc=False)
        temp_path = root.joinpath(f"{PARSED_FILE_NAME}.tmp")
        with open(temp_path, "wb") as pd:
            pickle.dump(doc, pd)
        temp_path.rename(root.joinpath(PARSED_FILE_NAME))
    except Exception as e:
        logger.warning(f"Could not parse {root} \n {e}")


if __name__ == "__main__":
    # Get all PDFs
    pdf_entries = []
    failed = []
    for root, directories, filenames in CACHE_PATH.walk():
        if filenames and "meta" in filenames:
            try:
                with open(root.joinpath("meta"), "r") as f:
                    meta = ast.literal_eval(f.read())
                if meta.get("url", "").endswith(".pdf"):
                    pdf_entries.append((root, meta["url"]))
            except Exception as e:
                failed.append((root, e))

    # Parallel extraction
    with get_context("spawn").Pool(cpu_count(), initializer=init_worker) as pool:
        list(tqdm(pool.imap(extract_pdf, pdf_entries, chunksize=10), 
                  total=len(pdf_entries), 
                  desc="Parsing PDFs"))