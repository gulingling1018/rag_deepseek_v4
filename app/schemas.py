from datetime import datetime

from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    id: str
    title: str
    filename: str
    source_path: str
    source_type: str = "file"
    source_url: str | None = None
    source_format: str | None = None
    encoding: str | None = None
    page_count: int | None = None
    doc_type: str = "other"
    content_domain: str | None = None
    chip_family: str | None = None
    version: str | None = None
    language: str | None = None
    is_entrypoint: bool = False
    retrieval_priority: int = 0
    chunk_count: int
    created_at: datetime


class ChunkRecord(BaseModel):
    id: str
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    block_type: str = "text"
    symbol_name: str | None = None
    doc_type: str = "other"
    content_domain: str | None = None
    chip_family: str | None = None
    version: str | None = None
    language: str | None = None
    is_entrypoint: bool = False
    retrieval_priority: int = 0
    section_path: list[str] = Field(default_factory=list)
    page_number: int | None = None
    page_label: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    source_uri: str | None = None
    location_label: str | None = None
    context_before: str | None = None
    context_after: str | None = None
    table_parse_confidence: str | None = None


class VectorRecord(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    provider: str = "hash"
    model: str = "hash-v1"
    dimension: int
    values: list[float] = Field(default_factory=list)


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str | None = None
    history: list[ChatTurn] = Field(default_factory=list)
    top_k: int | None = Field(default=None, ge=1, le=10)


class UrlImportRequest(BaseModel):
    url: str = Field(min_length=1)
    title: str | None = None


class Citation(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    block_type: str = "text"
    symbol_name: str | None = None
    doc_type: str = "other"
    chip_family: str | None = None
    section_path: list[str] = Field(default_factory=list)
    page_number: int | None = None
    page_label: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    source_uri: str | None = None
    location_label: str | None = None
    context_before: str | None = None
    context_after: str | None = None
    table_parse_confidence: str | None = None
    snippet: str
    content: str = Field(default="", exclude=True)
    score: float


class ChatResponse(BaseModel):
    answer: str
    session_id: str | None = None
    session_title: str | None = None
    citations: list[Citation]
    retrieved_chunks: int
    reasoning: str | None = None


class SessionCreateRequest(BaseModel):
    title: str | None = None


class SessionRecord(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message: str | None = None
    turn_count: int = 0


class SessionDetail(SessionRecord):
    messages: list[ChatTurn] = Field(default_factory=list)
