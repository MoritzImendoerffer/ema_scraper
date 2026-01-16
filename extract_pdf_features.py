import glob
from ema_scraper import settings
import ast
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from parsers.pdf_parser import DocumentStyleExtractor
from sklearn.feature_extraction.text import CountVectorizer
import pickle
BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")

# Worker function (must be at module level for pickling)
def extract_pdf(args):
    root, url, n_pages = args
    extractor = DocumentStyleExtractor(n_pages=n_pages)
    try:
        with open(root.joinpath("response_body"), "rb") as r:
            response = r.read()
        profile = extractor.extract(response, doc_id=url)
        return (root, profile)
    except Exception as e:
        return (root, None)
    
def extract_save_feature():
    # First pass: collect PDF entries
    pdf_entries = []
    failed = []
    for root, directories, filenames in CACHE_PATH.walk():
        if filenames and "meta" in filenames:
            try:
                with open(root.joinpath("meta"), "r") as f:
                    meta = ast.literal_eval(f.read())
                if meta.get("url", "").endswith(".pdf"):
                    pdf_entries.append((root, meta["url"], 10))  # 10 = n_pages
            except Exception as e:
                failed.append((root, e))
    # Second pass: parallel extraction
    results = []
    with Pool(cpu_count()) as pool:
        for result in tqdm(pool.imap(extract_pdf, pdf_entries), total=len(pdf_entries), desc="Extracting styles"):
            results.append(result)

        # Filter out failures
        results = [(root, profile) for root, profile in results if profile is not None]
        with open(BASE_PATH.joinpath("pdf_profile.pickle"), "wb") as f:
            pickle.dump(results, f)

if __name__ == "__main__":
    extract_save_feature()