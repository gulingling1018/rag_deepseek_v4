#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.importers import extract_document_from_path, extract_web_document
from app.schemas import ChunkRecord, DocumentRecord
from app.storage import JSONStorage


def main():
    parser = argparse.ArgumentParser(description="Rebuild document chunks and optionally vectors.")
    parser.add_argument(
        "--skip-vectors",
        action="store_true",
        help="Only rebuild documents/chunks and clear vectors. Run a vector rebuild after quality checks.",
    )
    parser.add_argument(
        "--title-contains",
        default=None,
        help="Only rebuild documents whose title contains this text. Useful for parser quality checks.",
    )
    args = parser.parse_args()

    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    documents = storage.list_documents()
    if args.title_contains:
        documents = [document for document in documents if args.title_contains in document.title]

    rebuilt_documents: list[DocumentRecord] = []
    rebuilt_chunks: list[ChunkRecord] = []

    for document in documents:
        print(f"reindexing: {document.title}", flush=True)
        if document.source_type == "url" and document.source_url:
            try:
                title, extracted = extract_web_document(document.source_url)
            except Exception:
                extracted = extract_document_from_path(Path(document.source_path))
                title = document.title
            rebuilt_document, chunks = storage.build_document_payload(
                filename=document.filename,
                source_path=document.source_path,
                text=extracted.text,
                title=document.title or title,
                source_type=document.source_type,
                source_url=document.source_url,
                source_format=extracted.source_format,
                encoding=extracted.encoding,
                blocks=[block.__dict__ for block in extracted.blocks],
                page_count=extracted.page_count,
                document_id=document.id,
                created_at=document.created_at,
            )
        else:
            extracted = extract_document_from_path(Path(document.source_path))
            rebuilt_document, chunks = storage.build_document_payload(
                filename=document.filename,
                source_path=document.source_path,
                text=extracted.text,
                title=document.title,
                source_type=document.source_type,
                source_url=document.source_url,
                source_format=extracted.source_format,
                encoding=extracted.encoding,
                blocks=[block.__dict__ for block in extracted.blocks],
                page_count=extracted.page_count,
                document_id=document.id,
                created_at=document.created_at,
            )

        rebuilt_documents.append(rebuilt_document)
        rebuilt_chunks.extend(chunks)
        print(
            f"reindexed: {rebuilt_document.title} "
            f"(pages={rebuilt_document.page_count}, chunks={rebuilt_document.chunk_count})",
            flush=True,
        )

    storage.rebuild_indexes(
        rebuilt_documents,
        rebuilt_chunks,
        rebuild_vectors=not args.skip_vectors,
    ) if not args.title_contains else None
    vector_status = "skipped" if args.skip_vectors else "rebuilt"
    if args.title_contains:
        print(
            f"dry_run_done: documents={len(rebuilt_documents)}, chunks={len(rebuilt_chunks)}, "
            "index_not_modified=true",
            flush=True,
        )
    else:
        print(f"done: documents={len(rebuilt_documents)}, chunks={len(rebuilt_chunks)}, vectors={vector_status}", flush=True)


if __name__ == "__main__":
    main()
