from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings
from app.retrieval_core import build_weighted_chunk_text
from app.schemas import ChunkRecord


@dataclass
class RerankResult:
    chunk: ChunkRecord
    score: float


class RerankerService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.rag_rerank_provider.lower()
        self.client = httpx.Client(timeout=60.0, trust_env=False)

    @property
    def enabled(self) -> bool:
        return self.provider != "none"

    def rerank(self, query: str, candidates: list[tuple[ChunkRecord, float]], top_k: int) -> list[tuple[ChunkRecord, float]]:
        if not candidates:
            return []
        if not self.enabled:
            return candidates[:top_k]
        try:
            if self.provider == "jina":
                return self._rerank_with_jina(query, candidates, top_k)
            if self.provider == "dashscope":
                return self._rerank_with_dashscope(query, candidates, top_k)
        except Exception:
            return candidates[:top_k]
        return candidates[:top_k]

    @staticmethod
    def _candidate_documents(candidates: list[tuple[ChunkRecord, float]]) -> list[str]:
        # Keep reranker requests comfortably below per-document token limits.
        return [build_weighted_chunk_text(chunk)[:6000] for chunk, _ in candidates]

    def _rerank_with_jina(self, query: str, candidates: list[tuple[ChunkRecord, float]], top_k: int) -> list[tuple[ChunkRecord, float]]:
        api_key = self.settings.rag_rerank_api_key
        if not api_key:
            return candidates[:top_k]

        limited = candidates[: self.settings.rag_rerank_candidate_limit]
        payload = {
            "model": self.settings.rag_rerank_model,
            "query": query,
            "top_n": min(top_k, len(limited)),
            "documents": self._candidate_documents(limited),
            "return_documents": False,
        }
        response = self.client.post(
            self.settings.rag_rerank_base_url.rstrip("/") + "/rerank",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        reranked: list[tuple[ChunkRecord, float]] = []
        for item in results:
            index = int(item.get("index", -1))
            if index < 0 or index >= len(limited):
                continue
            score = float(item.get("relevance_score", item.get("score", 0.0)))
            reranked.append((limited[index][0], score))
        return reranked or limited[:top_k]

    def _rerank_with_dashscope(self, query: str, candidates: list[tuple[ChunkRecord, float]], top_k: int) -> list[tuple[ChunkRecord, float]]:
        api_key = self.settings.rag_rerank_api_key or self.settings.deepseek_api_key
        if not api_key:
            return candidates[:top_k]

        limited = candidates[: self.settings.rag_rerank_candidate_limit]
        payload = {
            "model": self.settings.rag_rerank_model,
            "query": query,
            "documents": self._candidate_documents(limited),
            "top_n": min(top_k, len(limited)),
        }
        response = self.client.post(
            self.settings.rag_rerank_base_url.rstrip("/") + "/reranks",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        reranked: list[tuple[ChunkRecord, float]] = []
        for item in results:
            index = int(item.get("index", -1))
            if index < 0 or index >= len(limited):
                continue
            score = float(item.get("relevance_score", item.get("score", 0.0)))
            reranked.append((limited[index][0], score))
        return reranked or limited[:top_k]
