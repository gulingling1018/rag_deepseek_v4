from datetime import UTC, datetime
from pathlib import Path
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.deepseek_client import DeepSeekChatClient
from app.document_metadata import build_lookup_variants, normalize_lookup
from app.embeddings import EmbeddingService
from app.importers import extract_document_from_path, extract_web_document
from app.reranking import RerankerService
from app.retriever import HybridIndex
from app.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    SessionCreateRequest,
    UrlImportRequest,
)
from app.session_store import SessionStore
from app.storage import JSONStorage

app = FastAPI(title="DeepSeek RAG", version="0.3.0")
settings = get_settings()
storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
chat_client = DeepSeekChatClient(settings)
session_store = SessionStore(settings.rag_sessions_path)
embedding_service = EmbeddingService(settings)
reranker_service = RerankerService(settings)


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(filename).name)
    return cleaned or "upload.txt"


def resolve_target_document_ids(question: str) -> set[str]:
    normalized_question = normalize_lookup(question)
    matched: set[str] = set()
    for document in storage.list_documents():
        candidates = build_lookup_variants(
            document.title,
            document.filename,
            document.source_path,
            Path(document.source_path).name,
        )
        if any(candidate and len(candidate) >= 6 and candidate in normalized_question for candidate in candidates):
            matched.add(document.id)
    return matched


def should_include_low_signal_catalog(question: str) -> bool:
    normalized_question = normalize_lookup(question)
    catalog_terms = ("文档页", "产品页", "产品文档", "选型", "系列", "有哪些资料", "总览", "catalog")
    return any(term in normalized_question for term in catalog_terms)


def should_scope_to_bluetooth(question: str) -> bool:
    normalized_question = normalize_lookup(question)
    bluetooth_terms = ("蓝牙", "ble", "bluetooth", "nimble", "bluedroid", "gatt", "gap", "spp", "a2dp", "blufi", "br/edr")
    return any(term in normalized_question for term in bluetooth_terms)


def should_scope_to_code(question: str) -> bool:
    normalized_question = normalize_lookup(question)
    code_terms = ("代码", "源码", "实现", "函数", "方法", "类", "模块", "组件", "文件", "目录", "main.c", "app_main", "cmakelists", "kconfig", "sdkconfig", "menuconfig", "示例代码")
    return any(term in normalized_question for term in code_terms)


def extract_identifier_hints(question: str) -> set[str]:
    candidates = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", question))
    ignored = {"esp32", "ble", "bluetooth", "nimble", "bluedroid", "guide", "api", "scope", "code"}
    return {
        candidate.lower()
        for candidate in candidates
        if "_" in candidate or any(char.isupper() for char in candidate[1:]) or candidate.lower() not in ignored
    }


def is_bluetooth_chunk(chunk) -> bool:
    lookup = normalize_lookup(
        "\n".join(
            [
                chunk.document_title,
                " > ".join(chunk.section_path),
                chunk.content[:800],
            ]
        )
    )
    bluetooth_terms = ("蓝牙", "ble", "bluetooth", "nimble", "bluedroid", "gatt", "gap", "spp", "a2dp", "blufi", "br/edr")
    return any(term in lookup for term in bluetooth_terms)


def is_code_chunk(chunk) -> bool:
    if chunk.doc_type in {"source_code", "build_config", "project_config", "project_doc"}:
        return True
    if chunk.block_type == "code" or chunk.symbol_name or chunk.line_start is not None:
        return True
    lookup = normalize_lookup(
        "\n".join(
            [
                chunk.document_title,
                " > ".join(chunk.section_path),
                chunk.content[:800],
            ]
        )
    )
    code_terms = ("app_main", "cmakelists", "kconfig", "sdkconfig", "idf_component_register", "#include", "void ", "static ", "def ", "class ")
    return any(term in lookup for term in code_terms)


def matches_identifier_hint(chunk, identifiers: set[str]) -> bool:
    if not identifiers:
        return False
    lookup = normalize_lookup(
        "\n".join(
            [
                chunk.symbol_name or "",
                chunk.document_title,
                " > ".join(chunk.section_path),
                chunk.content[:1000],
            ]
        )
    )
    return any(identifier in lookup for identifier in identifiers)


def expand_chunk_content(chunk, chunk_lookup: dict[tuple[str, int], object]) -> str:
    base = chunk.content.strip()
    if not base:
        return ""

    if chunk.doc_type not in {"source_code", "build_config", "project_config", "project_doc"} and chunk.block_type != "code":
        return base

    pieces: list[str] = []
    for offset in (-1, 0, 1):
        neighbor = chunk_lookup.get((chunk.document_id, chunk.chunk_index + offset))
        if not neighbor:
            continue
        if neighbor.document_id != chunk.document_id:
            continue
        if offset == 0:
            pieces.append(neighbor.content.strip())
            continue
        if neighbor.block_type == chunk.block_type:
            pieces.append(neighbor.content.strip())

    merged = "\n\n".join(piece for piece in pieces if piece)
    return merged or base


def build_citations(question: str, history, top_k: int) -> list[Citation]:
    chunks = storage.list_chunks()
    vectors = storage.list_vectors()
    identifier_hints = extract_identifier_hints(question)
    target_document_ids = resolve_target_document_ids(question)
    if target_document_ids:
        chunks = [chunk for chunk in chunks if chunk.document_id in target_document_ids]
        vectors = [vector for vector in vectors if vector.document_id in target_document_ids]
    elif not should_include_low_signal_catalog(question):
        low_signal_types = {"catalog", "product_catalog"}
        chunks = [chunk for chunk in chunks if chunk.doc_type not in low_signal_types]
        allowed_document_ids = {chunk.document_id for chunk in chunks}
        vectors = [vector for vector in vectors if vector.document_id in allowed_document_ids]
        if should_scope_to_bluetooth(question) and not identifier_hints:
            bluetooth_chunks = [chunk for chunk in chunks if is_bluetooth_chunk(chunk)]
            if bluetooth_chunks:
                chunks = bluetooth_chunks
                allowed_document_ids = {chunk.document_id for chunk in chunks}
                vectors = [vector for vector in vectors if vector.document_id in allowed_document_ids]
        if should_scope_to_code(question):
            code_chunks = [chunk for chunk in chunks if is_code_chunk(chunk)]
            if code_chunks:
                chunks = code_chunks
                allowed_document_ids = {chunk.document_id for chunk in chunks}
                vectors = [vector for vector in vectors if vector.document_id in allowed_document_ids]
            if identifier_hints:
                identifier_chunks = [chunk for chunk in chunks if matches_identifier_hint(chunk, identifier_hints)]
                if identifier_chunks:
                    chunks = identifier_chunks
                    allowed_document_ids = {chunk.document_id for chunk in chunks}
                    vectors = [vector for vector in vectors if vector.document_id in allowed_document_ids]
                exact_symbol_chunks = [
                    chunk for chunk in chunks
                    if chunk.symbol_name and chunk.symbol_name.lower() in identifier_hints
                ]
                if exact_symbol_chunks:
                    ordered = sorted(
                        exact_symbol_chunks,
                        key=lambda chunk: (
                            chunk.document_title,
                            chunk.symbol_name or "",
                            chunk.chunk_index,
                        ),
                    )
                    chunk_lookup = {(chunk.document_id, chunk.chunk_index): chunk for chunk in chunks}
                    citations: list[Citation] = []
                    for rank, chunk in enumerate(ordered[:top_k], start=1):
                        snippet = chunk.content.strip()
                        if len(snippet) > 320:
                            snippet = f"{snippet[:320].rstrip()}..."
                        citations.append(
                            Citation(
                                document_id=chunk.document_id,
                                document_title=chunk.document_title,
                                chunk_id=chunk.id,
                                chunk_index=chunk.chunk_index,
                                block_type=chunk.block_type,
                                symbol_name=chunk.symbol_name,
                                doc_type=chunk.doc_type,
                                chip_family=chunk.chip_family,
                                section_path=chunk.section_path,
                                page_number=chunk.page_number,
                                page_label=chunk.page_label,
                                line_start=chunk.line_start,
                                line_end=chunk.line_end,
                                paragraph_start=chunk.paragraph_start,
                                paragraph_end=chunk.paragraph_end,
                                source_uri=chunk.source_uri,
                                location_label=chunk.location_label,
                                snippet=snippet,
                                content=expand_chunk_content(chunk, chunk_lookup),
                                score=round(1.0 - rank * 0.01, 4),
                            )
                        )
                    return citations
    index = HybridIndex(
        chunks,
        vectors=vectors,
        embedding_service=embedding_service,
        bm25_weight=settings.rag_hybrid_bm25_weight,
        vector_weight=settings.rag_hybrid_vector_weight,
    )
    candidate_limit = max(top_k, settings.rag_retrieval_candidate_limit)
    candidates = index.search(question, history=history, top_k=candidate_limit)
    results = reranker_service.rerank(question, candidates, top_k=top_k)
    chunk_lookup = {(chunk.document_id, chunk.chunk_index): chunk for chunk in chunks}
    citations: list[Citation] = []
    for chunk, score in results:
        snippet = chunk.content.strip()
        if len(snippet) > 320:
            snippet = f"{snippet[:320].rstrip()}..."
        citations.append(
            Citation(
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                block_type=chunk.block_type,
                symbol_name=chunk.symbol_name,
                doc_type=chunk.doc_type,
                chip_family=chunk.chip_family,
                section_path=chunk.section_path,
                page_number=chunk.page_number,
                page_label=chunk.page_label,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                paragraph_start=chunk.paragraph_start,
                paragraph_end=chunk.paragraph_end,
                source_uri=chunk.source_uri,
                location_label=chunk.location_label,
                snippet=snippet,
                content=expand_chunk_content(chunk, chunk_lookup),
                score=round(score, 4),
            )
        )
    return citations


def load_index_html() -> str:
    html_path = Path(__file__).resolve().parent / "ui" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": settings.deepseek_model,
        "retriever": "hybrid-bm25-vector",
        "embedding_provider": embedding_service.spec.provider,
        "embedding_model": embedding_service.spec.model,
        "vector_dim": str(embedding_service.spec.dimension),
        "reranker": settings.rag_rerank_provider,
        "time": datetime.now(UTC).isoformat(),
    }


@app.get("/api/documents")
def list_documents():
    return storage.list_documents()


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空。")

    safe_name = sanitize_filename(file.filename)
    stamped_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{safe_name}"
    destination = Path(settings.rag_upload_dir) / stamped_name
    content = await file.read()
    destination.write_bytes(content)

    try:
        extracted = extract_document_from_path(destination)
        document = storage.add_document(
            filename=file.filename,
            source_path=str(destination),
            text=extracted.text,
            source_format=extracted.source_format,
            encoding=extracted.encoding,
            blocks=[block.__dict__ for block in extracted.blocks],
            page_count=extracted.page_count,
        )
    except Exception as exc:
        if destination.exists():
            destination.unlink()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "文档已导入并建立索引。", "document": document}


@app.post("/api/documents/import-url")
def import_url_document(request: UrlImportRequest):
    existing = storage.find_document_by_source_url(request.url)
    if existing:
        return {"message": "该网页已存在于知识库中。", "document": existing}

    try:
        page_title, extracted = extract_web_document(request.url)
        title = request.title or page_title
        safe_name = sanitize_filename(f"{title}.md")
        stamped_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{safe_name}"
        destination = Path(settings.rag_upload_dir) / stamped_name
        destination.write_text(extracted.text, encoding="utf-8")
        document = storage.add_document(
            filename=safe_name,
            source_path=str(destination),
            text=extracted.text,
            title=title,
            source_type="url",
            source_url=request.url,
            source_format=extracted.source_format,
            encoding=extracted.encoding,
            blocks=[block.__dict__ for block in extracted.blocks],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "网页已导入并建立索引。", "document": document}


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    if not storage.delete_document(document_id):
        raise HTTPException(status_code=404, detail="文档不存在。")
    return {"message": "文档已删除。"}


@app.get("/api/sessions")
def list_sessions():
    return session_store.list_sessions()


@app.post("/api/sessions")
def create_session(request: SessionCreateRequest | None = None):
    title = request.title if request else None
    return session_store.create_session(title=title)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return session


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    if not session_store.delete_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在。")
    return {"message": "会话已删除。"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session = None
    if request.session_id:
        session = session_store.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在。")
    else:
        session = session_store.create_session()
        session = session_store.get_session(session.id)

    if session is None:
        raise HTTPException(status_code=500, detail="会话初始化失败。")

    if not session.messages and request.history:
        seeded = session_store.seed_history(session.id, request.history)
        if seeded:
            session = seeded

    citations = build_citations(
        question=request.question,
        history=session.messages,
        top_k=request.top_k or settings.rag_top_k,
    )
    answer, reasoning = chat_client.answer(
        question=request.question,
        citations=citations,
        history=session.messages,
    )

    updated_session = session_store.append_exchange(
        session_id=session.id,
        question=request.question,
        answer=answer,
    )
    if not updated_session:
        raise HTTPException(status_code=500, detail="写入会话失败。")

    return ChatResponse(
        answer=answer,
        session_id=updated_session.id,
        session_title=updated_session.title,
        citations=citations,
        retrieved_chunks=len(citations),
        reasoning=reasoning,
    )


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(load_index_html())
