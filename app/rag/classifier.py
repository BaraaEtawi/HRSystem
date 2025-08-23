from __future__ import annotations
from typing import Tuple
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer, util
from app.core.config import settings


HR_KEYWORDS = {
    "leave", "annual", "vacation", "holiday", "payroll", "salary", "benefit",
    "probation", "timesheet", "overtime", "sick", "per diem", "expense",
    "remote", "onsite", "attendance", "policy"
}


IT_KEYWORDS = {
    "vpn", "password", "account", "email", "laptop", "device", "hardware",
    "software", "access", "network", "security", "mfa", "2fa", "ticket",
    "backup", "antivirus", "data"
}


class DomainClassifier:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        hr_text = Path("data/hr_policy.md").read_text(encoding="utf-8")
        it_text = Path("data/it_policy.md").read_text(encoding="utf-8")
        self.hr_emb = self.model.encode(hr_text, convert_to_tensor=True, normalize_embeddings=True)
        self.it_emb = self.model.encode(it_text, convert_to_tensor=True, normalize_embeddings=True)

    def _keyword_score(self, q: str) -> Tuple[int, int]:
        ql = q.lower()
        hr_hits = sum(1 for w in HR_KEYWORDS if w in ql)
        it_hits = sum(1 for w in IT_KEYWORDS if w in ql)
        return hr_hits, it_hits

    def classify(self, q: str) -> Tuple[str, float, str]:
        hr_hits, it_hits = self._keyword_score(q)
        if hr_hits or it_hits:
            if hr_hits > it_hits:
                conf = min(0.9, 0.6 + 0.1 * (hr_hits - it_hits))
                return "HR", conf, "keywords"
            elif it_hits > hr_hits:
                conf = min(0.9, 0.6 + 0.1 * (it_hits - hr_hits))
                return "IT", conf, "keywords"

        q_emb = self.model.encode(q, convert_to_tensor=True, normalize_embeddings=True)
        sim_hr = float(util.cos_sim(q_emb, self.hr_emb).item())
        sim_it = float(util.cos_sim(q_emb, self.it_emb).item())
        if sim_hr >= sim_it:
            domain = "HR"
            diff = sim_hr - sim_it
        else:
            domain = "IT"
            diff = sim_it - sim_hr
        conf = max(0.5, min(0.95, 0.5 + diff))
        return domain, conf, "embeddings"