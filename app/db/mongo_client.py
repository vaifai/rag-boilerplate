from pymongo import MongoClient
from app.core.config import settings
from typing import Optional


class MongoClientWrapper:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB]
        self.chunks = self.db["chunks"]
        self.documents = self.db["documents"]
        self.runs = self.db["runs"]
        self.preferences = self.db["preferences"]

    def insert_chunk(self, chunk_doc: dict):
        """chunk_doc should contain keys: id, doc_id, title, category, text, backend_indexed (list)"""
        self.chunks.replace_one({"id": chunk_doc["id"]}, chunk_doc, upsert=True)

    def insert_document(self, doc: dict):
        self.documents.replace_one({"id": doc["id"]}, doc, upsert=True)

    def log_run(self, run_doc: dict):
        self.runs.insert_one(run_doc)

    def insert_preference(self, pref_doc: dict):
        # pref_doc: {user_id, query, chosen_pipeline, options, timestamp, reason?}
        self.preferences.insert_one(pref_doc)

    def get_chunk(self, chunk_id: str) -> Optional[dict]:
        return self.chunks.find_one({"id": chunk_id})
