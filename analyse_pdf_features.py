
from ema_scraper import settings

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import cupy as cp
from cuml.manifold import UMAP
from cuml.preprocessing import normalize
from cuml.cluster import HDBSCAN

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

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

umap_n_neighbors=20
umap_min_dist=1e-3
umap_spread=2.0
umap_n_epochs=500
umap_random_state=42

hdbscan_min_samples=25
hdbscan_min_cluster_size=10
hdbscan_max_cluster_size=1000
hdbscan_cluster_selection_method="leaf"

Xnorm = normalize(cp.array(X))

umap = UMAP(n_neighbors=umap_n_neighbors, 
            min_dist=umap_min_dist, 
            spread=umap_spread, 
            n_epochs=umap_n_epochs, 
            random_state=umap_random_state)

embeddings = umap.fit_transform(X)

hdbscan = HDBSCAN(min_samples=hdbscan_min_samples, 
                  min_cluster_size=hdbscan_min_cluster_size, 
                  max_cluster_size=hdbscan_max_cluster_size,
                  cluster_selection_method=hdbscan_cluster_selection_method)

labels = hdbscan.fit_predict(Xnorm)

with open(BASE_PATH.joinpath("predicted_labels.pkl"), "wb") as f:
    pickle.dump(labels, f)
