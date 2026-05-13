from __future__ import annotations

from app.document_ir import DocumentIR, IRBlock


LEGACY_BLOCK_TYPES = {"text", "table", "toc", "code", "formula"}


def legacy_block_type_for_role(role: str) -> str:
    normalized = (role or "text").strip().lower()
    if normalized in LEGACY_BLOCK_TYPES:
        return normalized
    if normalized in {"heading", "caption", "footnote"}:
        return "text"
    if normalized in {"header_footer", "noise"}:
        return "text"
    return "text"


def document_ir_to_legacy_chunk_payloads(document_ir: DocumentIR) -> list[dict]:
    return [ir_block_to_legacy_chunk_payload(block) for block in document_ir.blocks if block.text.strip()]


def ir_block_to_legacy_chunk_payload(block: IRBlock) -> dict:
    payload = {
        "block_id": block.block_id,
        "content": block.text,
        "block_type": legacy_block_type_for_role(block.role),
        "symbol_name": block.symbol_name,
        "section_path": list(block.section_path),
        "page_number": block.page_number,
        "page_label": block.attributes.get("page_label") if block.attributes else None,
        "line_start": block.line_start,
        "line_end": block.line_end,
        "paragraph_start": block.paragraph_start,
        "paragraph_end": block.paragraph_end,
        "source_uri": block.source_uri,
        "location_label": block.location_label,
        "context_before": block.attributes.get("context_before") if block.attributes else None,
        "context_after": block.attributes.get("context_after") if block.attributes else None,
        "parent_block_id": block.parent_id,
        "order_on_page": block.order_on_page,
        "page_region": block.page_region,
        "role_confidence": block.role_confidence,
        "extraction_confidence": block.extraction_confidence,
    }
    return payload
