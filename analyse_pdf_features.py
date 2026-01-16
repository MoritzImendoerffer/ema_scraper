import glob
from ema_scraper import settings
import ast
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from parsers.pdf_parser import DocumentStyleExtractor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from extract_pdf_features import extract_save_feature
from sklearn.decomposition import TruncatedSVD

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")

file_path = BASE_PATH.joinpath("pdf_profile.pickle")

if file_path.exists:
    with open(file_path, "rb") as f:
        results = pickle.load(f)
else:
    extract_save_feature()
    with open(file_path, "rb") as f:
        results = pickle.load(f)

   
# Vectorize
token_strings = [" ".join(profile[1].tokens) for profile in results]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(token_strings)
print(f"Done. Extracted {len(results)} profiles, {X.shape[1]} features")

dbscan = DBSCAN(eps=1, min_samples=10, metric="cosine")
dbscan.fit(X)
print("Done")