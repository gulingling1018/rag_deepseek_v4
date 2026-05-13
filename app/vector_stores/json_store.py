from __future__ import annotations

import json
from pathlib import Path

from app.schemas import ChunkRecord, VectorRecord
from app.vector_store import VectorSearchHit, VectorStore


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


class JsonVectorStore(VectorStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def list_records(
        self,
        *,
        collection_id: str | None = None,
        active_only: bool = False,
    ) -> list[VectorRecord]:
        records = [VectorRecord.model_validate(item) for item in self._read_json()]
        if collection_id is not None:
            records = [record for record in records if record.collection_id == collection_id]
        if active_only:
            records = [record for record in records if record.is_active]
        return records

    def write_records(
        self,
        records: list[VectorRecord],
        *,
        collection_id: str | None = None,
    ) -> None:
        if collection_id is None:
            self._write_json([record.model_dump(mode="json") for record in records])
            return

        existing = self.list_records()
        kept = [record for record in existing if record.collection_id != collection_id]
        kept.extend(records)
        self._write_json([record.model_dump(mode="json") for record in kept])

    def upsert(
        self,
        records: list[VectorRecord],
        *,
        collection_id: str,
    ) -> None:
        existing = self.list_records()
        record_map = {
            (record.collection_id, record.chunk_id): record
            for record in existing
        }
        for record in records:
            record_map[(collection_id, record.chunk_id)] = record.model_copy(update={"collection_id": collection_id})
        self._write_json([record.model_dump(mode="json") for record in record_map.values()])

    def delete_by_document(
        self,
        document_id: str,
        *,
        collection_id: str | None = None,
    ) -> None:
        kept = []
        for record in self.list_records():
            if record.document_id != document_id:
                kept.append(record)
                continue
            if collection_id is not None and record.collection_id != collection_id:
                kept.append(record)
        self._write_json([record.model_dump(mode="json") for record in kept])

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
        filters = filters or {}
        document_ids = set(filters.get("document_ids") or [])
        chunk_ids = set(filters.get("chunk_ids") or [])
        records = self.list_records(collection_id=collection_id, active_only=True)
        scored: list[VectorSearchHit] = []
        for record in records:
            if expected_provider is not None and record.provider != expected_provider:
                continue
            if expected_model is not None and record.model != expected_model:
                continue
            if expected_dimension is not None and record.dimension != expected_dimension:
                continue
            if document_ids and record.document_id not in document_ids:
                continue
            if chunk_ids and record.chunk_id not in chunk_ids:
                continue
            score = cosine_similarity(query_vector, record.values)
            if score > 0:
                scored.append(VectorSearchHit(chunk_id=record.chunk_id, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def validate_consistency(
        self,
        chunks: list[ChunkRecord],
        *,
        collection_id: str | None = None,
    ) -> dict[str, int]:
        records = self.list_records(collection_id=collection_id)
        chunk_map = {chunk.id: chunk for chunk in chunks}
        missing_vectors = 0
        stale_vectors = 0
        orphan_vectors = 0

        vector_map = {record.chunk_id: record for record in records if record.is_active}
        for chunk_id in chunk_map:
            if chunk_id not in vector_map:
                missing_vectors += 1

        for record in records:
            chunk = chunk_map.get(record.chunk_id)
            if chunk is None:
                orphan_vectors += 1
                continue
            if record.chunk_hash and record.chunk_hash != self._chunk_hash(chunk):
                stale_vectors += 1

        return {
            "chunks": len(chunks),
            "vectors": len(records),
            "missing_vectors": missing_vectors,
            "stale_vectors": stale_vectors,
            "orphan_vectors": orphan_vectors,
        }

    @staticmethod
    def _chunk_hash(chunk: ChunkRecord) -> str:
        import hashlib

        payload = "\n".join(
            [
                chunk.content,
                "|".join(chunk.section_path),
                chunk.page_label or "",
                chunk.location_label or "",
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _read_json(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write_json(self, payload: list[dict]) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
