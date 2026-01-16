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
    pickle.dump(result, f)
    
# Vectorize
token_strings = [" ".join(profile[1].tokens) for profile in results]

vectorizer = CountVectorizer(lowercase=False, max_features=1000)
X = vectorizer.fit_transform(token_strings)
print(f"Done. Extracted {len(results)} profiles, {X.shape[1]} features")

from sklearn.decomposition import TruncatedSVD

def reduce_dimensions(X, n_components: int = 100):
    """Reduce dimensionality before clustering."""
    print(f"Reducing dimensions: {X.shape[1]} → {n_components}")
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_reduced = svd.fit_transform(X)
    explained = svd.explained_variance_ratio_.sum()
    print(f"Explained variance: {explained:.1%}")
    return X_reduced, svd

X_reduced, svd = reduce_dimensions(X, n_components=100)

dbscan = DBSCAN(eps=0.1, min_samples=10, metric="cosine")
labels = dbscan.fit_predict(X)
print("Done")