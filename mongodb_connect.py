from pymongo import MongoClient
import regex as re

MONGI_URL = "localhost:21017"
MONGO_DB = "ema_scraper"
MONGO_COL = "web_items"

def connect():
    """Connect to MongoDB and return collection"""
    client = MongoClient(f"mongodb://{MONGI_URL}")
    db = client[MONGO_DB]
    collection = db[MONGO_COL]
    print(f"Connected to {MONGO_DB}.{MONGO_COL}")
    return collection

def get_keys_with_regex(collection, key, pattern, inverse=False):
    """
    Get keys from MongoDB collection using regex patterns
    
    :param collection: MongoDB collection
    :param key: key to retrieve
    :param pattern: regex pattern for searching
    :param inverse: Inverses the search {not: {"$regex": pattern}}
    """
    
    if inverse:
        query = {key: {"$not": {"$regex": pattern}}}
    else:
        query = {key: {"$regex": pattern}}

    result = collection.find(query)
    
    return result
    
if __name__ == "__main__":
    mc = connect()
    
    print("Done")