#!/usr/bin/env python3
import json
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.embeddings import EmbeddingService
from app.retrieval_core import build_weighted_chunk_text
from app.schemas import VectorRecord
from app.storage import JSONStorage


def main() -> None:
    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    chunks = storage.list_chunks()
    service = EmbeddingService(settings)
    spec = service.spec
    batch_size = max(1, settings.rag_embedding_batch_size)
    if "dashscope.aliyuncs.com" in settings.rag_embedding_base_url:
        batch_size = min(batch_size, 10)

    records: list[dict] = []
    start_time = time.time()
    print(
        f"rebuild_vectors_start chunks={len(chunks)} "
        f"provider={spec.provider} model={spec.model} dim={spec.dimension} batch={batch_size}",
        flush=True,
    )

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        texts = [build_weighted_chunk_text(chunk) for chunk in batch]
        vectors = service.embed_texts(texts)
        records.extend(
            VectorRecord(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                provider=spec.provider,
                model=spec.model,
                dimension=spec.dimension,
                values=values,
            ).model_dump(mode="json")
            for chunk, values in zip(batch, vectors, strict=False)
        )
        done = min(start + len(batch), len(chunks))
        if done == len(chunks) or done % (batch_size * 20) == 0:
            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed else 0.0
            print(f"progress {done}/{len(chunks)} elapsed={elapsed:.1f}s rate={rate:.1f}/s", flush=True)

    vectors_path = Path(settings.rag_index_dir) / "vectors.json"
    tmp_path = vectors_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp_path.replace(vectors_path)
    print(
        f"rebuild_vectors_done records={len(records)} seconds={time.time() - start_time:.1f} path={vectors_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
