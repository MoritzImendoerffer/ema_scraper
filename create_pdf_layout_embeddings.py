
from ema_scraper import settings

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")

file_path = BASE_PATH.joinpath("pdf_profile.pickle")

if file_path.exists:
    with open(file_path, "rb") as f:
        results = pickle.load(f)
else:
    #extract_save_feature()
    # with open(file_path, "rb") as f:
    #     results = pickle.load(f)
    print("Run ectract_pdf_features first")

   
# Vectorize
token_strings = [" ".join(profile[1].tokens) for profile in results]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(token_strings)
print(f"Done. Extracted {len(results)} profiles, {X.shape[1]} features")