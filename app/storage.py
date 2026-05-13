import json
import re
from datetime import datetime, UTC
from pathlib import Path
from threading import Lock
from uuid import uuid4
from typing import Any

from app.chunking import chunk_text
from app.chunk_profiles import resolve_chunk_profile
from app.chunk_strategies import build_default_chunk_strategy_registry
from app.config import get_settings
from app.content_quality import clean_section_path, is_bad_table, table_parse_confidence
from app.document_ir import DocumentIR
from app.document_metadata import derive_document_metadata
from app.embeddings import build_vector_records
from app.schemas import ChunkRecord, DocumentRecord, VectorRecord
from app.vector_stores.json_store import JsonVectorStore


class JSONStorage:
    def __init__(self, upload_dir: str, index_dir: str):
        self.upload_dir = Path(upload_dir)
        self.index_dir = Path(index_dir)
        self.documents_path = self.index_dir / "documents.json"
        self.chunks_path = self.index_dir / "chunks.json"
        self.vectors_path = self.index_dir / "vectors.json"
        self.lock = Lock()
        self.settings = get_settings()
        self.chunk_strategy_registry = build_default_chunk_strategy_registry()
        self.vector_store = JsonVectorStore(self.vectors_path)

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def list_documents(self) -> list[DocumentRecord]:
        return [
            DocumentRecord.model_validate(record)
            for record in self._read_json(self.documents_path, default=[])
        ]

    def list_chunks(self) -> list[ChunkRecord]:
        return [
            ChunkRecord.model_validate(record)
            for record in self._read_json(self.chunks_path, default=[])
        ]

    def list_vectors(self) -> list[VectorRecord]:
        return self.vector_store.list_records()

    def add_document(
        self,
        filename: str,
        source_path: str,
        text: str | None = None,
        *,
        title: str | None = None,
        source_type: str = "file",
        source_url: str | None = None,
        source_format: str | None = None,
        encoding: str | None = None,
        document_ir: DocumentIR | None = None,
        blocks: list[dict[str, Any]] | None = None,
        page_texts: list[dict[str, Any]] | None = None,
        page_count: int | None = None,
    ) -> DocumentRecord:
        document, chunk_records = self._build_document_and_chunks(
            filename=filename,
            source_path=source_path,
            text=text,
            title=title,
            source_type=source_type,
            source_url=source_url,
            source_format=source_format,
            encoding=encoding,
            document_ir=document_ir,
            blocks=blocks,
            page_texts=page_texts,
            page_count=page_count,
        )

        with self.lock:
            documents = self._read_json(self.documents_path, default=[])
            stored_chunks = self._read_json(self.chunks_path, default=[])
            documents.append(document.model_dump(mode="json"))
            stored_chunks.extend(item.model_dump(mode="json") for item in chunk_records)
            self._write_json(self.documents_path, documents)
            self._write_json(self.chunks_path, stored_chunks)
            self.vector_store.upsert(
                self.build_vectors(chunk_records),
                collection_id=self.settings.rag_vector_collection,
            )

        return document

    def rebuild_indexes(
        self,
        documents: list[DocumentRecord],
        chunks: list[ChunkRecord],
        *,
        rebuild_vectors: bool = True,
    ) -> None:
        with self.lock:
            self._write_json(
                self.documents_path,
                [item.model_dump(mode="json") for item in documents],
            )
            self._write_json(
                self.chunks_path,
                [item.model_dump(mode="json") for item in chunks],
            )
            vectors = self.build_vectors(chunks) if rebuild_vectors else []
            self.vector_store.write_records(
                vectors,
                collection_id=self.settings.rag_vector_collection if rebuild_vectors else None,
            )

    def find_document_by_source_url(self, source_url: str) -> DocumentRecord | None:
        for record in self._read_json(self.documents_path, default=[]):
            if record.get("source_url") == source_url:
                return DocumentRecord.model_validate(record)
        return None

    def find_document_by_source_path(self, source_path: str) -> DocumentRecord | None:
        target = Path(source_path).resolve()
        for record in self._read_json(self.documents_path, default=[]):
            record_path = Path(record.get("source_path", "")).resolve()
            if record_path == target:
                return DocumentRecord.model_validate(record)
        return None

    def delete_document(self, document_id: str) -> bool:
        with self.lock:
            documents = self._read_json(self.documents_path, default=[])
            chunks = self._read_json(self.chunks_path, default=[])
            kept_documents = [item for item in documents if item["id"] != document_id]
            if len(kept_documents) == len(documents):
                return False

            removed_document = next(item for item in documents if item["id"] == document_id)
            kept_chunks = [item for item in chunks if item["document_id"] != document_id]
            self._write_json(self.documents_path, kept_documents)
            self._write_json(self.chunks_path, kept_chunks)
            self.vector_store.delete_by_document(
                document_id,
                collection_id=self.settings.rag_vector_collection,
            )

        source_path = Path(removed_document["source_path"])
        upload_root = self.upload_dir.resolve()
        should_delete_file = False
        try:
            should_delete_file = source_path.resolve().is_relative_to(upload_root)
        except Exception:
            should_delete_file = False
        if should_delete_file and source_path.exists():
            source_path.unlink()
        return True

    def build_document_payload(
        self,
        *,
        filename: str,
        source_path: str,
        text: str | None = None,
        title: str | None = None,
        source_type: str = "file",
        source_url: str | None = None,
        source_format: str | None = None,
        encoding: str | None = None,
        document_ir: DocumentIR | None = None,
        blocks: list[dict[str, Any]] | None = None,
        page_texts: list[dict[str, Any]] | None = None,
        page_count: int | None = None,
        document_id: str | None = None,
        created_at: datetime | None = None,
    ) -> tuple[DocumentRecord, list[ChunkRecord]]:
        return self._build_document_and_chunks(
            filename=filename,
            source_path=source_path,
            text=text,
            title=title,
            source_type=source_type,
            source_url=source_url,
            source_format=source_format,
            encoding=encoding,
            document_ir=document_ir,
            blocks=blocks,
            page_texts=page_texts,
            page_count=page_count,
            document_id=document_id,
            created_at=created_at,
        )

    def _build_document_and_chunks(
        self,
        *,
        filename: str,
        source_path: str,
        text: str | None,
        title: str | None,
        source_type: str,
        source_url: str | None,
        source_format: str | None,
        encoding: str | None,
        document_ir: DocumentIR | None,
        blocks: list[dict[str, Any]] | None,
        page_texts: list[dict[str, Any]] | None,
        page_count: int | None,
        document_id: str | None = None,
        created_at: datetime | None = None,
    ) -> tuple[DocumentRecord, list[ChunkRecord]]:
        chunk_payloads: list[dict[str, Any]] = []
        if document_ir is not None:
            profile = resolve_chunk_profile(
                document_ir,
                filename=filename,
                title=title,
                source_path=source_path,
                source_url=source_url,
            )
            strategy_name = str(profile.get("chunk_strategy") or "generic_text")
            strategy = self.chunk_strategy_registry.resolve(strategy_name)
            chunk_payloads.extend(strategy.build_chunk_payloads(document_ir))
        elif blocks:
            for block in blocks:
                block_type = self._normalize_optional_text(block.get("block_type")) or "text"
                content = self._normalize_chunk_content(
                    block.get("content", block.get("text", "")),
                    preserve_blank_lines=block_type == "code",
                )
                if not content:
                    continue
                if block_type == "table" and is_bad_table(content):
                    continue
                chunk_payloads.append(
                    {
                        "content": content,
                        "block_type": block_type,
                        "symbol_name": self._normalize_optional_text(block.get("symbol_name")),
                        "section_path": self._normalize_section_path(block.get("section_path", [])),
                        "page_number": block.get("page_number"),
                        "page_label": self._normalize_optional_text(block.get("page_label")),
                        "line_start": block.get("line_start"),
                        "line_end": block.get("line_end"),
                        "paragraph_start": block.get("paragraph_start"),
                        "paragraph_end": block.get("paragraph_end"),
                        "source_uri": self._normalize_optional_text(block.get("source_uri")),
                        "location_label": self._normalize_optional_text(block.get("location_label")),
                        "context_before": self._normalize_optional_text(block.get("context_before")),
                        "context_after": self._normalize_optional_text(block.get("context_after")),
                        "block_id": self._normalize_optional_text(block.get("block_id")),
                        "parent_block_id": self._normalize_optional_text(block.get("parent_block_id")),
                        "order_on_page": block.get("order_on_page"),
                        "page_region": self._normalize_optional_text(block.get("page_region")),
                        "role_confidence": block.get("role_confidence"),
                        "extraction_confidence": block.get("extraction_confidence"),
                    }
                )
        elif page_texts:
            for page in page_texts:
                page_chunks = chunk_text(page["text"])
                for chunk in page_chunks:
                    chunk_payloads.append(
                        {
                            "content": chunk,
                            "block_type": "text",
                            "symbol_name": None,
                            "section_path": [],
                            "page_number": page["page_number"],
                            "page_label": f"第 {page['page_number']} 页",
                            "line_start": None,
                            "line_end": None,
                            "paragraph_start": None,
                            "paragraph_end": None,
                            "source_uri": None,
                            "location_label": f"第 {page['page_number']} 页",
                            "context_before": None,
                            "context_after": None,
                        }
                    )
        elif text is not None:
            for chunk in chunk_text(text):
                chunk_payloads.append(
                        {
                            "content": chunk,
                            "block_type": "text",
                            "symbol_name": None,
                            "section_path": [],
                        "page_number": None,
                        "page_label": None,
                        "line_start": None,
                        "line_end": None,
                        "paragraph_start": None,
                        "paragraph_end": None,
                        "source_uri": None,
                        "location_label": None,
                        "context_before": None,
                        "context_after": None,
                    }
                )

        if not chunk_payloads:
            raise ValueError("文档内容为空，无法建立索引。")

        chunk_payloads = [self._finalize_chunk_payload(item) for item in chunk_payloads]
        if document_ir is None:
            chunk_payloads = self._attach_code_context_and_filter_connectors(chunk_payloads)
            chunk_payloads = self._merge_short_text_payloads(chunk_payloads)

        doc_id = document_id or uuid4().hex
        resolved_page_count = page_count
        if resolved_page_count is None and document_ir is not None and document_ir.pages:
            resolved_page_count = len(document_ir.pages)
        doc_title = title or (document_ir.title if document_ir is not None else None) or Path(filename).stem
        metadata = derive_document_metadata(
            filename=filename,
            title=doc_title,
            source_path=source_path,
            source_url=source_url,
            source_format=source_format,
            chunk_count=len(chunk_payloads),
        )
        document = DocumentRecord(
            id=doc_id,
            title=doc_title,
            filename=filename,
            source_path=source_path,
            source_type=source_type,
            source_url=source_url,
            source_format=source_format,
            encoding=encoding,
            page_count=resolved_page_count,
            doc_type=str(metadata["doc_type"]),
            content_domain=str(metadata["content_domain"]) if metadata["content_domain"] is not None else None,
            chip_family=str(metadata["chip_family"]) if metadata["chip_family"] is not None else None,
            version=str(metadata["version"]) if metadata["version"] is not None else None,
            language=str(metadata["language"]) if metadata["language"] is not None else None,
            is_entrypoint=bool(metadata["is_entrypoint"]),
            retrieval_priority=int(metadata["retrieval_priority"]),
            chunk_count=len(chunk_payloads),
            created_at=created_at or datetime.now(UTC),
        )
        chunk_records = [
            ChunkRecord(
                id=f"{doc_id}:{index}",
                document_id=doc_id,
                document_title=doc_title,
                chunk_index=index,
                block_id=item.get("block_id"),
                content=item["content"],
                block_type=item.get("block_type", "text"),
                symbol_name=item.get("symbol_name"),
                doc_type=document.doc_type,
                content_domain=document.content_domain,
                chip_family=document.chip_family,
                version=document.version,
                language=document.language,
                is_entrypoint=document.is_entrypoint,
                retrieval_priority=document.retrieval_priority,
                section_path=item.get("section_path", []),
                page_number=item["page_number"],
                page_label=item["page_label"],
                line_start=item.get("line_start"),
                line_end=item.get("line_end"),
                paragraph_start=item.get("paragraph_start"),
                paragraph_end=item.get("paragraph_end"),
                source_uri=item.get("source_uri"),
                location_label=item.get("location_label"),
                context_before=item.get("context_before"),
                context_after=item.get("context_after"),
                parent_block_id=item.get("parent_block_id"),
                order_on_page=item.get("order_on_page"),
                page_region=item.get("page_region"),
                role_confidence=item.get("role_confidence"),
                extraction_confidence=item.get("extraction_confidence"),
                table_parse_confidence=item.get("table_parse_confidence"),
            )
            for index, item in enumerate(chunk_payloads)
        ]
        return document, chunk_records

    def build_vectors(self, chunks: list[ChunkRecord]) -> list[VectorRecord]:
        return build_vector_records(chunks, self.settings)

    def validate_vector_consistency(self, chunks: list[ChunkRecord] | None = None) -> dict[str, int]:
        return self.vector_store.validate_consistency(
            chunks or self.list_chunks(),
            collection_id=self.settings.rag_vector_collection,
        )

    @staticmethod
    def _normalize_chunk_content(content: Any, preserve_blank_lines: bool = False) -> str:
        if content is None:
            return ""
        text = str(content).replace("\r\n", "\n").replace("\r", "\n")
        text = "\n".join(line.rstrip() for line in text.splitlines())
        if preserve_blank_lines:
            return text.strip("\n")
        text = "\n".join(line for line in text.splitlines() if line.strip())
        return text.strip()

    @staticmethod
    def _normalize_section_path(section_path: Any) -> list[str]:
        return clean_section_path(section_path)

    @staticmethod
    def _normalize_optional_text(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def _finalize_chunk_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        page_number = payload.get("page_number")
        line_start = payload.get("line_start")
        line_end = payload.get("line_end")
        paragraph_start = payload.get("paragraph_start")
        paragraph_end = payload.get("paragraph_end")
        location_label = payload.get("location_label")

        if not payload.get("page_label") and page_number is not None:
            payload["page_label"] = f"第 {page_number} 页"
        if line_start is not None and line_end is None:
            payload["line_end"] = line_start
        if paragraph_start is not None and paragraph_end is None:
            payload["paragraph_end"] = paragraph_start

        if not location_label:
            if line_start is not None and payload.get("line_end") is not None:
                line_end = payload["line_end"]
                payload["location_label"] = (
                    f"行 {line_start}" if line_start == line_end else f"行 {line_start}-{line_end}"
                )
            elif paragraph_start is not None and payload.get("paragraph_end") is not None:
                paragraph_end = payload["paragraph_end"]
                payload["location_label"] = (
                    f"段落 {paragraph_start}"
                    if paragraph_start == paragraph_end
                    else f"段落 {paragraph_start}-{paragraph_end}"
                )
            elif page_number is not None:
                payload["location_label"] = f"第 {page_number} 页"

        if payload.get("block_type") == "table":
            payload["table_parse_confidence"] = table_parse_confidence(payload.get("content", ""))

        return payload

    @staticmethod
    def _same_scope(left: dict[str, Any], right: dict[str, Any]) -> bool:
        return (
            left.get("section_path") == right.get("section_path")
            and left.get("page_number") == right.get("page_number")
            and left.get("source_uri") == right.get("source_uri")
        )

    @staticmethod
    def _is_short_code_payload(payload: dict[str, Any]) -> bool:
        if payload.get("block_type") != "code":
            return False
        content = payload.get("content", "")
        nonempty_lines = [line for line in content.splitlines() if line.strip()]
        return len(content) < 120 or len(nonempty_lines) == 1

    @staticmethod
    def _is_code_connector_text(text: str) -> bool:
        compact = re.sub(r"\s+", " ", text).strip()
        if not compact or len(compact) > 100:
            return False
        lowered = compact.lower()
        exact = {
            "or:",
            "for example:",
            "cmakelists.txt:",
            "minimal project:",
            "example:",
        }
        if lowered in exact:
            return True
        return bool(
            re.search(
                r"(?:is in|implementation is in|content of|file is|following|below)\s*[\w./+-]*:?\s*$",
                lowered,
            )
        )

    @staticmethod
    def _append_context(existing: str | None, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return existing or ""
        if existing:
            return f"{existing}\n{text}".strip()
        return text

    def _attach_code_context_and_filter_connectors(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        keep = [True] * len(payloads)
        for index, payload in enumerate(payloads):
            if not self._is_short_code_payload(payload):
                continue

            for direction, context_key in ((-1, "context_before"), (1, "context_after")):
                neighbor_index = index + direction
                if neighbor_index < 0 or neighbor_index >= len(payloads):
                    continue
                neighbor = payloads[neighbor_index]
                if neighbor.get("block_type") != "text":
                    continue
                if not self._same_scope(payload, neighbor):
                    continue
                neighbor_text = neighbor.get("content", "")
                if len(neighbor_text) > 500:
                    neighbor_text = neighbor_text[:500]
                payload[context_key] = self._append_context(payload.get(context_key), neighbor_text)
                if self._is_code_connector_text(neighbor.get("content", "")):
                    keep[neighbor_index] = False

        return [payload for payload, should_keep in zip(payloads, keep, strict=False) if should_keep]

    def _merge_short_text_payloads(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        index = 0
        while index < len(payloads):
            payload = payloads[index]
            content = payload.get("content", "")
            if payload.get("block_type") == "text" and len(content) < 50:
                if (
                    merged
                    and merged[-1].get("block_type") == "text"
                    and self._same_scope(merged[-1], payload)
                    and len(merged[-1].get("content", "")) + len(content) <= 1800
                ):
                    merged[-1]["content"] = f"{merged[-1]['content']}\n\n{content}".strip()
                    merged[-1]["line_end"] = payload.get("line_end") or merged[-1].get("line_end")
                    merged[-1]["paragraph_end"] = payload.get("paragraph_end") or merged[-1].get("paragraph_end")
                    index += 1
                    continue
                if index + 1 < len(payloads):
                    next_payload = payloads[index + 1]
                    if (
                        next_payload.get("block_type") == "text"
                        and self._same_scope(payload, next_payload)
                        and len(next_payload.get("content", "")) + len(content) <= 1800
                    ):
                        next_payload["content"] = f"{content}\n\n{next_payload['content']}".strip()
                        next_payload["line_start"] = payload.get("line_start") or next_payload.get("line_start")
                        next_payload["paragraph_start"] = payload.get("paragraph_start") or next_payload.get("paragraph_start")
                        index += 1
                        continue
            merged.append(payload)
            index += 1
        return merged

    @staticmethod
    def _read_json(path: Path, default: list[dict]) -> list[dict]:
        if not path.exists():
            return list(default)
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, value: list[dict]) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
