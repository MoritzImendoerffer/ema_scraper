from pymongo import MongoClient
 
# CONFIGURATION
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "ema_scraper"
MONGO_COL = "web_items"

def connect():
    """Connect to MongoDB and return collection"""
    client = MongoClient(MONGO_URI)
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