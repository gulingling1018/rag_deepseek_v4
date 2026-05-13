from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.document_ir import DocumentIR
from app.ir_adapters import document_ir_to_legacy_chunk_payloads


def same_scope(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("section_path") == right.get("section_path")
        and left.get("page_number") == right.get("page_number")
        and left.get("source_uri") == right.get("source_uri")
    )


def is_short_code_payload(payload: dict[str, Any]) -> bool:
    if payload.get("block_type") != "code":
        return False
    content = payload.get("content", "")
    nonempty_lines = [line for line in content.splitlines() if line.strip()]
    return len(content) < 120 or len(nonempty_lines) == 1


def is_code_connector_text(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact or len(compact) > 100:
        return False
    lowered = compact.lower()
    if lowered in {"or:", "for example:", "cmakelists.txt:", "minimal project:", "example:"}:
        return True
    return bool(
        re.search(
            r"(?:is in|implementation is in|content of|file is|following|below)\s*[\w./+-]*:?\s*$",
            lowered,
        )
    )


def append_context(existing: str | None, text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return existing or ""
    if existing:
        return f"{existing}\n{compact}".strip()
    return compact


def attach_code_context_and_filter_connectors(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keep = [True] * len(payloads)
    for index, payload in enumerate(payloads):
        if not is_short_code_payload(payload):
            continue

        for direction, context_key in ((-1, "context_before"), (1, "context_after")):
            neighbor_index = index + direction
            if neighbor_index < 0 or neighbor_index >= len(payloads):
                continue
            neighbor = payloads[neighbor_index]
            if neighbor.get("block_type") != "text":
                continue
            if not same_scope(payload, neighbor):
                continue
            neighbor_text = neighbor.get("content", "")
            if len(neighbor_text) > 500:
                neighbor_text = neighbor_text[:500]
            payload[context_key] = append_context(payload.get(context_key), neighbor_text)
            if is_code_connector_text(neighbor.get("content", "")):
                keep[neighbor_index] = False

    return [payload for payload, should_keep in zip(payloads, keep, strict=False) if should_keep]


def merge_short_text_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index = 0
    while index < len(payloads):
        payload = payloads[index]
        content = payload.get("content", "")
        if payload.get("block_type") == "text" and len(content) < 50:
            if (
                merged
                and merged[-1].get("block_type") == "text"
                and same_scope(merged[-1], payload)
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
                    and same_scope(payload, next_payload)
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


@dataclass
class ChunkStrategy:
    name: str

    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        raise NotImplementedError


class GenericTextChunkStrategy(ChunkStrategy):
    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        return merge_short_text_payloads(document_ir_to_legacy_chunk_payloads(document_ir))


class MarkdownGuideChunkStrategy(ChunkStrategy):
    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        return merge_short_text_payloads(document_ir_to_legacy_chunk_payloads(document_ir))


class WebArticleChunkStrategy(ChunkStrategy):
    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        return merge_short_text_payloads(document_ir_to_legacy_chunk_payloads(document_ir))


class PdfDocumentChunkStrategy(ChunkStrategy):
    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        return merge_short_text_payloads(document_ir_to_legacy_chunk_payloads(document_ir))


class SourceCodeChunkStrategy(ChunkStrategy):
    def build_chunk_payloads(self, document_ir: DocumentIR) -> list[dict[str, Any]]:
        payloads = document_ir_to_legacy_chunk_payloads(document_ir)
        payloads = attach_code_context_and_filter_connectors(payloads)
        return merge_short_text_payloads(payloads)


class ChunkStrategyRegistry:
    def __init__(self, strategies: list[ChunkStrategy]):
        self.strategies = {strategy.name: strategy for strategy in strategies}

    def resolve(self, strategy_name: str) -> ChunkStrategy:
        strategy = self.strategies.get(strategy_name)
        if strategy is None:
            strategy = self.strategies["generic_text"]
        return strategy


def build_default_chunk_strategy_registry() -> ChunkStrategyRegistry:
    return ChunkStrategyRegistry(
        [
            GenericTextChunkStrategy(name="generic_text"),
            MarkdownGuideChunkStrategy(name="markdown_guide"),
            WebArticleChunkStrategy(name="web_article"),
            PdfDocumentChunkStrategy(name="pdf_document"),
            SourceCodeChunkStrategy(name="source_code"),
        ]
    )
