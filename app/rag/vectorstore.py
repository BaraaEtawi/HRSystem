from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings


@dataclass
class RetrievedChunk:
    content: str
    metadata: Dict[str, Any]
    score: float  


class PolicyVectorStore:
    def __init__(self, collection_name: str = "policies"):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    def search(self, query: str, k: int = 5, domain: str | None = None) -> List[RetrievedChunk]:
        where = {"domain": domain} if domain else None
        res = self.collection.query(query_texts=[query], n_results=k, where=where)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        out: List[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            score = 1.0 - float(dist)
            out.append(RetrievedChunk(content=doc, metadata=meta, score=score))
        return out