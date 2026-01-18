import glob
from ema_scraper import settings
import ast
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from parsers.pdf_parser import DocumentStyleExtractor
from sklearn.feature_extraction.text import CountVectorizer
import pickle


from utils.cache_utils import get_files_from_cache, get_pdfs_from_cache

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")

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

# First pass: collect PDF entries
pdf_entries, failed = get_pdfs_from_cache()

# Second pass: parallel extraction
results = []
with Pool(cpu_count()) as pool:
    for result in tqdm(pool.imap(extract_pdf, pdf_entries), total=len(pdf_entries), desc="Extracting styles"):
        results.append(result)

# Filter out failures
results = [(root, profile) for root, profile in results if profile is not None]
with open(BASE_PATH.joinpath("pdf_profile.pickle"), "wb") as f:
    pickle.dump(result, f)
    
