from unittest.mock import patch


def test_vectorstore_search_filters_domain():
    from app.rag.vectorstore import PolicyVectorStore

    class DummyCollection:
        def query(self, query_texts, n_results, where=None):
            if where == {"domain": "HR"}:
                return {
                    "documents": [["doc1"]],
                    "metadatas": [[{"domain": "HR", "source": "hr_policy.md"}]],
                    "distances": [[0.2]],
                }
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    with patch("app.rag.vectorstore.chromadb.PersistentClient") as client:
        client.return_value.get_or_create_collection.return_value = DummyCollection()
        store = PolicyVectorStore()

    res = store.search("leave policy", k=1, domain="HR")
    assert len(res) == 1
    assert res[0].metadata.get("domain") == "HR"


def test_vectorstore_returns_scores_and_metadata():
    from app.rag.vectorstore import PolicyVectorStore

    class DummyCollection:
        def query(self, query_texts, n_results, where=None):
            return {
                "documents": [["Example content"]],
                "metadatas": [[{"domain": "IT", "source": "it_policy.md", "heading": "Passwords"}]],
                "distances": [[0.1]],
            }

    with patch("app.rag.vectorstore.chromadb.PersistentClient") as client:
        client.return_value.get_or_create_collection.return_value = DummyCollection()
        store = PolicyVectorStore()

    out = store.search("password rules", k=1, domain=None)
    assert len(out) == 1
    item = out[0]
    assert item.content == "Example content"
    assert item.metadata.get("source") == "it_policy.md"
    assert 0.0 <= item.score <= 1.0

