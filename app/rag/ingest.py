from __future__ import annotations
import pathlib
import hashlib
from typing import List, Dict
from app.rag.chunker import split_markdown
from app.rag.vectorstore import PolicyVectorStore


POLICIES = [
    {"domain": "HR", "path": "data/hr_policy.md"},
    {"domain": "IT", "path": "data/it_policy.md"},
]

def ingest() -> None:   
    store = PolicyVectorStore()

    ids: List[str] = []
    docs: List[str] = []
    metas: List[Dict] = []

    for item in POLICIES:
        domain = item["domain"]
        path = pathlib.Path(item["path"]).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")
        text = path.read_text(encoding="utf-8")
        chunks = split_markdown(text, max_chars=1000, overlap=150)
        for ch in chunks:
            to_hash = f"{ch.get('heading','')}\n{ch['content']}"
            h = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()[:12]
            ids.append(f"{domain}-{path.stem}-{h}")
            docs.append(ch["content"])
            metas.append({
                "domain": domain,
                "source": path.name,
                "heading": ch.get("heading") or "",
            })

    store.add(ids=ids, texts=docs, metadatas=metas)
    print(f"Ingested {len(docs)} chunks into Chroma collection '{store.collection.name}'")

if __name__ == "__main__":
    ingest()