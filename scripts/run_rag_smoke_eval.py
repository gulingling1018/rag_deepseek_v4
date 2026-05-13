#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.embeddings import EmbeddingService  # noqa: E402
from app.retriever import HybridIndex  # noqa: E402
from app.storage import JSONStorage  # noqa: E402


DEFAULT_QUESTIONS = PROJECT_ROOT / "data" / "reports" / "rag_smoke_questions.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "reports" / "rag_smoke_eval_results.json"


def normalize(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def snippet(text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:limit] + ("..." if len(compact) > limit else "")


def hit_at(results: list[dict], expected_documents: list[str], k: int) -> bool:
    expected = {normalize(item) for item in expected_documents}
    if not expected:
        return False
    return any(normalize(item["document_title"]) in expected for item in results[:k])


def reciprocal_rank(results: list[dict], expected_documents: list[str]) -> float:
    expected = {normalize(item) for item in expected_documents}
    if not expected:
        return 0.0
    for index, item in enumerate(results, start=1):
        if normalize(item["document_title"]) in expected:
            return 1.0 / index
    return 0.0


def term_coverage(results: list[dict], expected_terms: list[str], k: int) -> dict:
    merged = normalize("\n".join(item["content"] for item in results[:k]))
    matched = [term for term in expected_terms if normalize(term) in merged]
    return {
        "matched": matched,
        "missing": [term for term in expected_terms if term not in matched],
        "ratio": len(matched) / len(expected_terms) if expected_terms else 0.0,
    }


def summarize_results(per_question: list[dict], chunks_count: int, vectors_count: int, top_k: int, mode: str) -> dict:
    count = len(per_question) or 1
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ"),
        "mode": mode,
        "questions": len(per_question),
        "chunks": chunks_count,
        "vectors": vectors_count,
        "top_k": top_k,
        "hit_at_1": sum(1 for item in per_question if item["hit_at_1"]) / count,
        "hit_at_3": sum(1 for item in per_question if item["hit_at_3"]) / count,
        "hit_at_5": sum(1 for item in per_question if item["hit_at_5"]) / count,
        "mrr": sum(item["reciprocal_rank"] for item in per_question) / count,
        "term_coverage_at_5": sum(item["term_coverage_at_5"]["ratio"] for item in per_question) / count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run smoke retrieval checks over indexed chunks.")
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS), help="Path to rag_smoke_questions.json")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Where to write JSON results")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to inspect per question")
    parser.add_argument(
        "--mode",
        choices=["bm25", "vector", "hybrid", "all"],
        default="hybrid",
        help="Retrieval mode to evaluate. Use all to compare bm25/vector/hybrid in one output.",
    )
    args = parser.parse_args()

    questions_path = Path(args.questions)
    output_path = Path(args.output)
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    chunks = storage.list_chunks()
    vectors = storage.list_vectors()
    modes = ["bm25", "vector", "hybrid"] if args.mode == "all" else [args.mode]
    embedding_service = EmbeddingService(settings) if any(mode in {"vector", "hybrid"} for mode in modes) else None
    index = HybridIndex(chunks, vectors=vectors, embedding_service=embedding_service)

    payload_by_mode = {}
    for mode in modes:
        per_question = []
        for question in questions:
            if mode == "bm25":
                raw_results = index.bm25.search(question["question"], top_k=args.top_k)
            elif mode == "vector":
                raw_results = index.vector.search(question["question"], top_k=args.top_k)
            else:
                raw_results = index.search(question["question"], top_k=args.top_k)

            results = []
            for chunk, score in raw_results:
                results.append(
                    {
                        "score": round(score, 6),
                        "document_title": chunk.document_title,
                        "chunk_index": chunk.chunk_index,
                        "block_type": chunk.block_type,
                        "section_path": chunk.section_path,
                        "table_parse_confidence": chunk.table_parse_confidence,
                        "page_label": chunk.page_label,
                        "location_label": chunk.location_label,
                        "content": chunk.content,
                        "snippet": snippet(chunk.content),
                    }
                )
            expected_documents = question.get("expected_documents", [])
            expected_terms = question.get("expected_terms", [])
            per_question.append(
                {
                    "id": question["id"],
                    "question": question["question"],
                    "expected_documents": expected_documents,
                    "expected_terms": expected_terms,
                    "hit_at_1": hit_at(results, expected_documents, 1),
                    "hit_at_3": hit_at(results, expected_documents, 3),
                    "hit_at_5": hit_at(results, expected_documents, min(5, args.top_k)),
                    "reciprocal_rank": reciprocal_rank(results, expected_documents),
                    "term_coverage_at_5": term_coverage(results, expected_terms, min(5, args.top_k)),
                    "top_results": results,
                }
            )
        payload_by_mode[mode] = {
            "summary": summarize_results(per_question, len(chunks), len(vectors), args.top_k, mode),
            "questions": per_question,
        }

    payload = (
        payload_by_mode[modes[0]]
        if len(modes) == 1
        else {
            "summary_by_mode": {mode: data["summary"] for mode, data in payload_by_mode.items()},
            "results_by_mode": payload_by_mode,
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload.get("summary") or payload.get("summary_by_mode"), ensure_ascii=False, indent=2))
    print(f"wrote: {output_path}")


if __name__ == "__main__":
    main()
