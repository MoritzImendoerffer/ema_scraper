from pymongo import MongoClient
import regex as re
from urllib import parse
from lxml import html
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
from collections import defaultdict
from ema_scraper import settings as my_settings
from utils.mongo_utils import connect
from typing import Iterable
import pandas as pd
import pickle
# CONFIGURATION
HTML_FIELD = "html_raw"  # Field containing the raw HTML
URL_FIELD = "url"  # Field containing the source URL
TYPE_FIELD = "content_type"  # Field containing the content type

"""
# Aim

Analyse web pages based on their structure to find out how many different parser I need.
I did cluster the pages based on a fingerprint derived from it`s structure.

# Outcome
Interesting approach but not really useful or helpful. Individual parsers based on components might be better.
https://ec.europa.eu/component-library/ec/components/
https://github.com/openeuropa

I will test in dev_parsing_strategy.py
"""

def get_str_field(document, field, default=""):
    value = document.get(field, default)
    if isinstance(value, str):
        return value
    elif isinstance(value, Iterable):
        if len(value) != 1:
            raise ValueError(f"Return field has length > 1: {value}")
        raw_html = value[0]
        return raw_html
    else:
        raise NotImplementedError(f"Unknown type returned: {type(value)}")
    
def get_html_field(document):
    raw_html = get_str_field(document, HTML_FIELD, "")
    return raw_html

def get_url_field(document):
    uri = get_str_field(document, URL_FIELD, "")
    return uri

def get_url_parts():
    mc = connect()
    urls = mc.find({},{"url": 1})
    items = mc.find({TYPE_FIELD: "text/html"}, {"url": 1})
    lurl_html = list(items)
    
    url_list = []
    for item in lurl_html:
        url_list.append(item["url"][0])
            
    url_parts = []
    for item in lurl_html:
        up = parse.urlparse(item["url"][0])
        url_parts.append(up.path)
        
    url_tags = []
    for item in url_parts:
        parts = item.replace("/en/", "").split("/")
        if len(parts) == 1:
            url_tags.append(parts)
        else:
            url_tags.append(parts[0:-1])
    
    url_tags_set = set()
    for item in url_tags:
        url_tags_set.add("/".join(item))
    
    return url_list, url_parts, url_tags, url_tags_set

def get_root_tree_from_html(html_content, root_name=None):
    """
    Returns the lxml tree and if provided the root node for element root_name
    
    :param html_content: Description
    :param root_name: Description
    """
    if not html_content:
        print("Warning: no html content provided")
        return None
    
    tree = html.fromstring(html_content)
    
    # Focus only on the main content wrapper to reduce noise
    if root_name:
        root = tree.xpath(f'//*[contains(@class, "{root_name}")]')
        if not root:
            print("Warning: no root found. Parsing full html tree.")
            root = [tree]
    else:
        # Fallback if wrapper isn't found (might be a different template type)
        root = [tree]
        
    root_element = root[0]
    
    return tree, root_element
                 
def get_class_names(html_content, root_name=None):
    tree, root_element = get_root_tree_from_html(html_content, root_name)
    unique_classes = set()
    class_names = []
    for element in root_element.iter():
        unique_classes.update(element.classes)
        class_names.append(element.classes)
    return unique_classes, class_names

def get_structural_fingerprint(html_content, root_name=None):
    """
    Parses HTML and returns a string representing its structural 'skeleton'.
    It ignores text and focuses on the hierarchy of tags and classes within e.g. main_content_wrapper.
    """
    if not html_content:
        return ""

    try:
        tree, root_element = get_root_tree_from_html(html_content, root_name)
        
        paths = []
        doc_tree = root_element.getroottree()
        # Iterate over all elements to generate a "path signature"
        # Indices are stripped (div[1] -> div) to group lists together
        for element in root_element.iter():
            path = doc_tree.getpath(element)
            
            # Generalize the path: remove numeric indices [1], [2] 
            # This ensures a table with 5 rows looks the same as a table with 10 rows
            clean_path = '/'.join([p.split('[')[0] for p in path.split('/')])
            
            # Add class names to the path for higher fidelity
            # e.g., "div.node-content-wrapper" vs "div.sidebar"
            classes = element.get('class', '')
            if classes:
                classes = classes.replace(' ', '.')
                clean_path += f".{classes}"
                
            paths.append(clean_path)
        
        return paths

    except Exception as e:
        print(f"Error, could not convert tree: {e}")
        return ""
    
def get_web_docs(collection, sample_size=0):
    # Fetch data
    cursor = collection.find({TYPE_FIELD: "text/html"}, {HTML_FIELD: 1, URL_FIELD: 1})
    if sample_size > 0:
        cursor = cursor.limit(sample_size)
    return list(cursor)

def get_clases_from_db(root_name="main-content-wrapper"):
    collection = connect()
    documents = get_web_docs(collection)
    all_classes = []
    all_urls = []
    for doc in documents:
        raw_html = get_html_field(doc)
        all_urls.append(get_url_field(doc))
        cn, uc = get_class_names(raw_html, root_name)
        all_classes.append(cn)
    
    return documents, all_classes, all_urls
        
def get_tree(root_name=None):
    collection = connect()
    documents = get_web_docs(collection)
    print(f"Loaded {len(documents)} documents.")

    print("Generating Structural Fingerprints...")
    fingerprints = []
    valid_docs = []

    for doc in documents:
        raw_html = get_html_field(doc)
        fp = get_structural_fingerprint(raw_html, root_name=root_name)
        if fp:
            fingerprints.append(fp)
            valid_docs.append(doc)

    print(f"Successfully fingerprinted {len(valid_docs)} documents.")

    return valid_docs, fingerprints

def vectorize_tree(fingerprints):
    # Vectorization, conversion the paths into a numerical matrix
    print("Vectorizing Fingerprints")
    vectorizer = CountVectorizer(binary=True, max_features=10000)
    X = vectorizer.fit_transform(fingerprints)
    return X, vectorizer

def cluster_tree(X, eps=0.5, min_samples=5, metric="cosine"):
    # Clustering
    # eps: The maximum distance between two samples for one to be considered as in the neighborhood of the other.
    # min_samples: The number of samples in a neighborhood for a point to be considered as a core point.
    print("Running DBSCAN Clustering")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
    labels = dbscan.fit_predict(X)
    print("Finished DBSCAN Clustering")
    return dbscan, labels

def analyse_clusters(labels, valid_docs):
    # Analysis
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    print(f"Estimated number of unique templates: {n_clusters}")
    print(f"Outliers (unique/broken pages): {n_noise}")

    # Group URLs by Cluster ID
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(valid_docs[idx].get(URL_FIELD, "N/A"))
    return clusters, n_clusters, n_noise

def print_clusters(clusters):
    for label in sorted(clusters.keys()):
        urls = clusters[label]
        count = len(urls)
        
        if label == -1:
            label_name = "NOISE (Unique Pages)"
        else:
            label_name = f"Cluster {label}"

        print(f"\n{label_name} | Count: {count}")
        # Print some wURLs for manual inspection
        for url in urls[:3]:
            print(f"  - {url}")
            
def save_clusters(clusters, file_name="clusters.xlsx"):
    base_path = my_settings.BASE_PATH
    with pd.ExcelWriter(base_path.joinpath(file_name), engine="openpyxl") as f:
        for key, values in clusters.items():
            _df = pd.DataFrame(values)
            _df.to_excel(excel_writer=f, sheet_name=str(key))
        
def picke_save(object, file_name="fingerprints.pkl"):
      base_path = my_settings.BASE_PATH
      with open(base_path.joinpath(file_name), "wb") as f:
          pickle.dump(object, f)
          
if __name__ == "__main__":
    documents, class_names, urls = get_clases_from_db(root_name="main-content-wrapper")
    unique_classes = set([subitem for item in class_names for subitem in item])
    # treat fingerprints as sentences for vectorizer
    # fingerprint_class_names = [" ".join(item) for item in class_names]
    # class_names_set_sorted = sorted([list(set(item)) for item in class_names], key = lambda x: len(x))
    # X, vectorizer = vectorize_tree(fingerprint_class_names)
    
    # dscan, labels = cluster_tree(X, eps=0.075, min_samples=10)
    # clusters, n_clusters, n_noise = analyse_clusters(labels, documents)
    # print_clusters(clusters)
    # save_clusters(clusters, file_name="simple_cluster.xlsx")
    
    # docs, fingerprints = get_tree(root_name="main-content-wrapper")
    # # treat fingerprints as sentences for vectorizer
    # fingerprints_joined = [" ".join(item) for item in fingerprints]
    # Xp, vectorizerp = vectorize_tree(fingerprints_joined)
    # dscanp, labelsp = cluster_tree(Xp, eps=0.075, min_samples=10)
    # clustersp, n_clustersp, n_noisep = analyse_clusters(labelsp, docs)
    
    # print_clusters(clustersp)
    # save_clusters(clustersp, file_name="tree_cluster.xlsx")
    # url_list, url_parts, url_tags, url_tags_set = get_url_parts()