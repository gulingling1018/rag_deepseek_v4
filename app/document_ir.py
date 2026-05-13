from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LayoutBox:
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None
    page_width: float | None = None
    page_height: float | None = None


@dataclass
class IRPage:
    page_number: int
    page_label: str | None = None
    width: float | None = None
    height: float | None = None
    extraction_confidence: float | None = None
    used_ocr: bool = False


@dataclass
class IRBlock:
    block_id: str
    page_number: int | None
    role: str
    text: str
    section_path: list[str] = field(default_factory=list)
    bbox: LayoutBox | None = None
    parent_id: str | None = None
    order_on_page: int | None = None
    page_region: str | None = None
    role_confidence: float | None = None
    extraction_confidence: float | None = None
    source_uri: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    location_label: str | None = None
    symbol_name: str | None = None
    attributes: dict[str, str | int | float | bool | None] = field(default_factory=dict)


@dataclass
class DocumentIR:
    document_id: str | None
    source_type: str
    source_format: str
    title: str
    pages: list[IRPage] = field(default_factory=list)
    blocks: list[IRBlock] = field(default_factory=list)
    quality_signals: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    metadata_hints: dict[str, str | int | float | bool | None] = field(default_factory=dict)
