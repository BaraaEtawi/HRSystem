from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str = ""
    heading: str = ""
    snippet: str = ""


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    domain: str
    confidence: float
    answer: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    retrieval_scores: List[float] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification: Optional[str] = None
    latency_ms: int
    input_token_count: Optional[int] = None
    input_char_count: Optional[int] = None
    output_token_count: Optional[int] = None
    output_char_count: Optional[int] = None

