from unittest.mock import patch


def test_keyword_classification_hr():
    from app.rag import classifier as mod

    class DummyModel:
        def encode(self, *args, **kwargs):
            return [0]

    with patch.object(mod, "SentenceTransformer", return_value=DummyModel()):
        with patch.object(mod.util, "cos_sim", return_value=[[0.0]]):
            clf = mod.DomainClassifier()

    domain, conf, method = clf.classify("sick leave policy and annual leave")
    assert domain == "HR"
    assert conf >= 0.5
    assert method in {"keywords", "embeddings"}


def test_keyword_classification_it():
    from app.rag import classifier as mod

    class DummyModel:
        def encode(self, *args, **kwargs):
            return [0]

    with patch.object(mod, "SentenceTransformer", return_value=DummyModel()):
        with patch.object(mod.util, "cos_sim", return_value=[[0.0]]):
            clf = mod.DomainClassifier()

    domain, conf, method = clf.classify("password policy for laptop encryption")
    assert domain == "IT"
    assert conf >= 0.5
    assert method in {"keywords", "embeddings"}



