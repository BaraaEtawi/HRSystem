from __future__ import annotations
import time
from typing import List
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.rag.classifier import DomainClassifier
from app.rag.vectorstore import PolicyVectorStore
from app.rag.generator import AnswerGenerator


router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("app.chat")

_classifier: DomainClassifier | None = None
_generator: AnswerGenerator | None = None
_store: PolicyVectorStore | None = None


def _get_classifier() -> DomainClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DomainClassifier()
    return _classifier


def _get_generator() -> AnswerGenerator:
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator


def _get_store() -> PolicyVectorStore:
    global _store
    if _store is None:
        _store = PolicyVectorStore()
    return _store


def _redact(text: str, max_len: int = 500) -> str:
    t = (text or "").strip()
    return (t[:max_len] + "…") if len(t) > max_len else t


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, user=Depends(get_current_user)):
    q = (req.question or "").strip()
    if not (1 <= len(q) <= 500):
        raise HTTPException(status_code=422, detail="question must be 1–500 characters")
    t0 = time.time()

    clf = _get_classifier()
    domain, conf, method = clf.classify(req.question)

    if conf < 0.55:
        return ChatResponse(
            domain=domain,
            confidence=conf,
            answer=None,
            needs_clarification=True,
            clarification="Is your question about HR policy (leave, payroll, benefits) or IT policy (accounts, devices, security)?",
            citations=[],
            retrieval_scores=[],
            latency_ms=int((time.time() - t0) * 1000),
        )

    store = _get_store()
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(store.search, q, 6, domain=domain),
            timeout=settings.VECTOR_TIMEOUT_SECONDS,
        )
    except Exception:
        raise HTTPException(status_code=503, detail="vector store unavailable")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="vector store timeout")

    if not results:
        return ChatResponse(
            domain=domain,
            confidence=conf,
            answer=None,
            citations=[],
            retrieval_scores=[],
            needs_clarification=True,
            clarification="I couldn't find relevant policy content. Could you rephrase or add details?",
            latency_ms=int((time.time() - t0) * 1000),
        )

    top_score = max(r.score for r in results)
    if top_score < 0.3:
        return ChatResponse(
            domain=domain,
            confidence=conf,
            answer=None,
            citations=[],
            retrieval_scores=[round(r.score, 4) for r in results],
            needs_clarification=True,
            clarification="I found only weak matches. Can you clarify what exactly you need?",
            latency_ms=int((time.time() - t0) * 1000),
        )

    sorted_res = sorted(results, key=lambda r: r.score, reverse=True)
    best_score = sorted_res[0].score if sorted_res else 0.0
    seen = set()
    dedup = []
    for r in sorted_res:
        key = (r.metadata.get("heading", "") or "").strip().lower()
        key = " ".join(key.split())
        if not key:
            key = (r.content[:120].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)
        if len(dedup) >= 3:
            break
    top = dedup
    context_blocks = [r.content for r in top]

    gen = _get_generator()
    try:
        answer = await asyncio.wait_for(
            asyncio.to_thread(gen.generate, q, context_blocks),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    except Exception:
        raise HTTPException(status_code=503, detail="LLM temporarily unavailable")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="LLM timeout")

    citations: List[Citation] = [
        Citation(
            source=r.metadata.get("source", ""),
            heading=r.metadata.get("heading", ""),
            snippet=(r.content[:200] + ("..." if len(r.content) > 200 else "")),
        )
        for r in top
    ]

    qtext = req.question or ""
    input_char_count = len(qtext)
    input_token_count = len(qtext.split())
    out_char_count = len(answer) if answer else 0
    out_token_count = len(answer.split()) if answer else 0

    try:
        logger.info(
            {
                "question": _redact(q, 300),
                "answer": _redact(answer, 800),
                "request_id": getattr(request.state, "request_id", None),
                "latency_ms": int((time.time() - t0) * 1000),
                "domain": domain,
                "confidence": round(conf, 3),
                "top_score": round(best_score, 4),
                "retrieved_k": 6,
                "final_top_k": len(top),
                "status": "success",
            }
        )
    except Exception:
        pass

    return ChatResponse(
        domain=domain,
        confidence=round(conf, 3),
        answer=answer,
        citations=citations,
        retrieval_scores=[round(r.score, 4) for r in results],
        latency_ms=int((time.time() - t0) * 1000),
        input_token_count=input_token_count,
        input_char_count=input_char_count,
        output_token_count=out_token_count,
        output_char_count=out_char_count,
    )

