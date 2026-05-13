from __future__ import annotations

from dataclasses import dataclass

import httpx
from openai import OpenAI

from app.config import Settings
from app.retrieval_core import build_weighted_chunk_text, vectorize_text_hash
from app.schemas import ChunkRecord, VectorRecord


@dataclass
class EmbeddingSpec:
    provider: str
    model: str
    dimension: int


class EmbeddingService:
    OPENAI_COMPAT_INPUT_LIMIT = 7500

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.rag_embedding_provider.lower()
        self.client: OpenAI | None = None
        if self.provider == "openai":
            self.client = OpenAI(
                api_key=settings.rag_embedding_api_key or settings.deepseek_api_key,
                base_url=settings.rag_embedding_base_url,
                http_client=httpx.Client(timeout=60.0, trust_env=False),
            )

    @property
    def spec(self) -> EmbeddingSpec:
        if self.provider == "openai":
            dimension = self.settings.rag_embedding_dimensions or self.settings.rag_vector_dim
            return EmbeddingSpec(
                provider="openai",
                model=self.settings.rag_embedding_model,
                dimension=dimension,
            )
        return EmbeddingSpec(
            provider="hash",
            model="hash-v1",
            dimension=self.settings.rag_vector_dim,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "openai":
            return self._embed_texts_openai(texts)
        return [vectorize_text_hash(text, self.settings.rag_vector_dim) for text in texts]

    def _embed_texts_openai(self, texts: list[str]) -> list[list[float]]:
        if self.client is None:
            raise RuntimeError("OpenAI embedding client is not initialized.")

        outputs: list[list[float]] = []
        batch_size = max(1, self.settings.rag_embedding_batch_size)
        if "dashscope.aliyuncs.com" in self.settings.rag_embedding_base_url:
            batch_size = min(batch_size, 10)
        dimensions = self.settings.rag_embedding_dimensions or self.settings.rag_vector_dim
        for start in range(0, len(texts), batch_size):
            batch = [self._prepare_openai_compatible_input(text) for text in texts[start : start + batch_size]]
            payload: dict[str, object] = {
                "model": self.settings.rag_embedding_model,
                "input": batch,
            }
            if dimensions is not None:
                payload["dimensions"] = dimensions
            response = self.client.embeddings.create(**payload)
            ordered = sorted(response.data, key=lambda item: item.index)
            outputs.extend([list(item.embedding) for item in ordered])
        return outputs

    def _prepare_openai_compatible_input(self, text: str) -> str:
        cleaned = " ".join(text.split())
        if not cleaned:
            return " "
        limit = self.OPENAI_COMPAT_INPUT_LIMIT
        if len(cleaned) <= limit:
            return cleaned

        head_len = limit * 3 // 4
        tail_len = limit - head_len - 20
        return f"{cleaned[:head_len]} ... {cleaned[-tail_len:]}"


def build_vector_records(chunks: list[ChunkRecord], settings: Settings) -> list[VectorRecord]:
    if not chunks:
        return []

    service = EmbeddingService(settings)
    texts = [build_weighted_chunk_text(chunk) for chunk in chunks]
    vectors = service.embed_texts(texts)
    spec = service.spec
    return [
        VectorRecord(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            provider=spec.provider,
            model=spec.model,
            dimension=spec.dimension,
            values=values,
        )
        for chunk, values in zip(chunks, vectors, strict=False)
    ]
