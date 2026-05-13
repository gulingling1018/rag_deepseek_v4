from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = Field(..., alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    deepseek_enable_thinking: bool = Field(False, alias="DEEPSEEK_ENABLE_THINKING")

    rag_top_k: int = Field(5, alias="RAG_TOP_K")
    rag_max_history_messages: int = Field(6, alias="RAG_MAX_HISTORY_MESSAGES")
    rag_upload_dir: str = Field("./data/uploads", alias="RAG_UPLOAD_DIR")
    rag_index_dir: str = Field("./data/index", alias="RAG_INDEX_DIR")
    rag_sessions_path: str = Field("./data/index/sessions.json", alias="RAG_SESSIONS_PATH")
    rag_vector_dim: int = Field(384, alias="RAG_VECTOR_DIM")
    rag_hybrid_bm25_weight: float = Field(0.55, alias="RAG_HYBRID_BM25_WEIGHT")
    rag_hybrid_vector_weight: float = Field(0.45, alias="RAG_HYBRID_VECTOR_WEIGHT")
    rag_retrieval_candidate_limit: int = Field(40, alias="RAG_RETRIEVAL_CANDIDATE_LIMIT")
    rag_embedding_provider: str = Field("hash", alias="RAG_EMBEDDING_PROVIDER")
    rag_embedding_base_url: str = Field("https://api.openai.com/v1", alias="RAG_EMBEDDING_BASE_URL")
    rag_embedding_api_key: str | None = Field(None, alias="RAG_EMBEDDING_API_KEY")
    rag_embedding_model: str = Field("text-embedding-3-large", alias="RAG_EMBEDDING_MODEL")
    rag_embedding_dimensions: int | None = Field(None, alias="RAG_EMBEDDING_DIMENSIONS")
    rag_embedding_batch_size: int = Field(64, alias="RAG_EMBEDDING_BATCH_SIZE")
    rag_rerank_provider: str = Field("none", alias="RAG_RERANK_PROVIDER")
    rag_rerank_base_url: str = Field("https://api.jina.ai/v1", alias="RAG_RERANK_BASE_URL")
    rag_rerank_api_key: str | None = Field(None, alias="RAG_RERANK_API_KEY")
    rag_rerank_model: str = Field("jina-reranker-m0", alias="RAG_RERANK_MODEL")
    rag_rerank_candidate_limit: int = Field(40, alias="RAG_RERANK_CANDIDATE_LIMIT")
    rag_pdf_ocr_enabled: bool = Field(True, alias="RAG_PDF_OCR_ENABLED")
    rag_pdf_ocr_mode: str = Field("auto", alias="RAG_PDF_OCR_MODE")
    rag_pdf_ocr_dpi: int = Field(200, alias="RAG_PDF_OCR_DPI")
    rag_pdf_ocr_quality_threshold: float = Field(0.72, alias="RAG_PDF_OCR_QUALITY_THRESHOLD")


@lru_cache
def get_settings() -> Settings:
    return Settings()
