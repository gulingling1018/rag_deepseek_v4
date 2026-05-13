from __future__ import annotations

from dataclasses import dataclass

from app.schemas import ChunkRecord, VectorRecord


@dataclass
class VectorSearchHit:
    chunk_id: str
    score: float


class VectorStore:
    def list_records(
        self,
        *,
        collection_id: str | None = None,
        active_only: bool = False,
    ) -> list[VectorRecord]:
        raise NotImplementedError

    def write_records(
        self,
        records: list[VectorRecord],
        *,
        collection_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    def upsert(
        self,
        records: list[VectorRecord],
        *,
        collection_id: str,
    ) -> None:
        raise NotImplementedError

    def delete_by_document(
        self,
        document_id: str,
        *,
        collection_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        collection_id: str | None = None,
        filters: dict | None = None,
        expected_provider: str | None = None,
        expected_model: str | None = None,
        expected_dimension: int | None = None,
    ) -> list[VectorSearchHit]:
        raise NotImplementedError

    def validate_consistency(
        self,
        chunks: list[ChunkRecord],
        *,
        collection_id: str | None = None,
    ) -> dict[str, int]:
        raise NotImplementedError
