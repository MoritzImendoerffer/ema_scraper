# Before: storage/database.py (SQLite)
# After:  storage/mongodb.py

from pymongo import MongoClient
from dataclasses import dataclass, asdict

@dataclass
class DocumentRecord:
    url: str
    doc_type: str
    title: str = ""
    content: str = ""
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DocumentStore:
    def __init__(self, connection_string: str, db_name: str = "ema_rag"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.documents = self.db.documents
        self.links = self.db.links
        
        # Create indexes
        self.documents.create_index("url", unique=True)
        self.links.create_index([("source_url", 1), ("target_url", 1)])
    
    def add_document(self, doc: DocumentRecord):
        self.documents.update_one(
            {"url": doc.url},
            {"$set": asdict(doc)},
            upsert=True
        )
    
    def find_by_type(self, doc_type: str) -> list[dict]:
        return list(self.documents.find({"doc_type": doc_type}))
    
    def find_by_metadata(self, **kwargs) -> list[dict]:
        query = {f"metadata.{k}": v for k, v in kwargs.items()}
        return list(self.documents.find(query))