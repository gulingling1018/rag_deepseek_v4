#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.content_quality import is_bad_table, section_heading_level, table_parse_confidence, valid_section_title  # noqa: E402
from app.importers import is_probable_pdf_formula, pdf_formula_score, pdf_heading_score  # noqa: E402


REPORT_DIR = PROJECT_ROOT / "data" / "reports"
INDEX_DIR = PROJECT_ROOT / "data" / "index"

CODE_MARKERS = (
    "idf_component_register",
    "target_link_libraries",
    "externalproject_add",
    "add_custom_command",
    "set_target_properties",
    "${",
    "#include",
    "cmake_minimum_required",
)

PAGE_CHAR = "\u9875"
YEAR_CHAR = "\u5e74"
MONTH_CHAR = "\u6708"
PRINT_WORD = "\u5370\u5237"
ORDINAL_CHAR = "\u7b2c"
EDITION_CHAR = "\u7248"
FIGURE_CHAR = "\u56fe"
TABLE_CHAR = "\u8868"
VEHICLE_THEORY = "\u6c7d\u8f66\u7406\u8bba"


def read_json(name: str) -> list[dict]:
    path = INDEX_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def clean_one_line(text: object, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", str(text)).strip()
    return compact[:limit] + ("..." if len(compact) > limit else "")


def is_print_or_page_noise(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in ("z-library", "1lib", "z-lib")):
        return True
    if re.search(f"{ORDINAL_CHAR}\\s*\\d+\\s*{PAGE_CHAR}", text, re.IGNORECASE):
        return True
    if re.search(r"\bpage\s*\d+\b", text, re.IGNORECASE):
        return True
    if re.search(f"\\d{{4}}\\s*{YEAR_CHAR}\\s*\\d+\\s*{MONTH_CHAR}.*{PRINT_WORD}", text):
        return True
    if re.search(f"{ORDINAL_CHAR}\\s*\\d+\\s*{EDITION_CHAR}", text) and "\u524d\u8a00" not in text:
        return True
    return False


def section_issue(part: object) -> str | None:
    compact = clean_one_line(part, 500)
    lowered = compact.lower()
    if not valid_section_title(compact):
        return "invalid_title_rule"
    if is_print_or_page_noise(compact):
        return "page_or_print_noise"
    if re.match(f"^({FIGURE_CHAR}|{TABLE_CHAR}|figure|fig\\.|table)\\s*\\d", compact, re.IGNORECASE):
        return "figure_or_table_caption"
    if re.search(r"https?://|www\.", compact):
        return "url_in_section_path"
    if re.fullmatch(f"\\d+\\s*{VEHICLE_THEORY}", compact):
        return "running_header_or_repeated_title"
    if any(marker in lowered for marker in CODE_MARKERS):
        return "code_in_section_path"
    return None


def is_separator_row(row: str) -> bool:
    stripped = row.strip().strip("|").strip()
    if not stripped:
        return False
    return all(ch in "-:| " for ch in stripped) and "---" in stripped


def looks_like_formula_leakage(text: str) -> bool:
    return is_probable_pdf_formula(text)


def looks_like_bad_start(text: str) -> bool:
    stripped = re.sub(r"\s+", " ", text).strip()
    if len(stripped) < 30:
        return False
    if re.match(r"^[a-z]", stripped):
        return True
    if re.match(r"^(的|了|和|与|及|或|擦|系数|中心|距离|变形|关系|曲线|则|因此|所以|而|但|并)", stripped):
        return True
    if re.match(r"^[，,。.；;：:）)]", stripped):
        return True
    return False


def is_chapter_title(text: object) -> bool:
    compact = clean_one_line(text, 160)
    return section_heading_level(compact) == 1 and bool(
        re.match(f"^{ORDINAL_CHAR}\\s*[一二三四五六七八九十百零0-9]+\\s*章", compact)
        or re.match(r"^chapter\s+\d+\b", compact, flags=re.IGNORECASE)
    )


def chapter_transition_path_error(path: list[object]) -> bool:
    return sum(1 for part in path if is_chapter_title(part)) > 1


def candidate_heading_from_text(text: str, section_path: list[str]) -> str | None:
    lines = [clean_one_line(line, 160) for line in text.splitlines()[:3] if clean_one_line(line, 160)]
    path_text = "\n".join(section_path)
    for line in lines:
        score = pdf_heading_score(line)
        if 0.35 <= score < 0.55 and valid_section_title(line) and line not in path_text:
            return line
        if re.match(f"^{ORDINAL_CHAR}\\s*[一二三四五六七八九十百零0-9]+\\s*{EDITION_CHAR}\\s*前言$", line) and line not in path_text:
            return line
    return None


def add_example(bucket: dict[str, list[dict]], key: str, chunk: dict, detail: object = "", limit: int = 12) -> None:
    items = bucket.setdefault(key, [])
    if len(items) >= limit:
        return
    items.append(
        {
            "document_title": chunk.get("document_title"),
            "chunk_index": chunk.get("chunk_index"),
            "block_type": chunk.get("block_type"),
            "section_path": chunk.get("section_path") or [],
            "page_label": chunk.get("page_label"),
            "location_label": chunk.get("location_label"),
            "detail": clean_one_line(detail, 240) if detail else "",
            "snippet": clean_one_line(chunk.get("content", ""), 320),
        }
    )


def make_smoke_questions(pdf_title: str | None) -> list[dict]:
    pdf_docs = [pdf_title] if pdf_title else []
    return [
        {
            "id": "esp32_wireless_capabilities",
            "question": "ESP32 \u96c6\u6210\u4e86\u54ea\u4e9b\u65e0\u7ebf\u80fd\u529b\uff1f",
            "expected_documents": ["ESP32 Product Documentation", "ESP-IDF Get Started ESP32"],
            "expected_terms": ["Wi-Fi", "Bluetooth"],
            "intent": "product_overview",
        },
        {
            "id": "esp_idf_prerequisites",
            "question": "ESP-IDF \u5f00\u53d1\u73af\u5883\u9700\u8981\u54ea\u4e9b\u8f6f\u4ef6\u7ec4\u4ef6\uff1f",
            "expected_documents": ["ESP-IDF Get Started ESP32"],
            "expected_terms": ["ESP-IDF", "tools", "Python", "Git"],
            "intent": "guide_prerequisites",
        },
        {
            "id": "idf_py_build_equivalent",
            "question": "idf.py build \u7b49\u4ef7\u4e8e\u54ea\u4e9b CMake \u6216 Ninja \u547d\u4ee4\uff1f",
            "expected_documents": ["ESP-IDF Build System ESP32"],
            "expected_terms": ["cmake", "ninja", "build"],
            "intent": "code_command_mapping",
        },
        {
            "id": "idf_component_definition",
            "question": "ESP-IDF \u9879\u76ee\u4e2d\u7684 component \u662f\u4ec0\u4e48\uff1f",
            "expected_documents": ["ESP-IDF Build System ESP32"],
            "expected_terms": ["component", "CMakeLists.txt"],
            "intent": "concept_definition",
        },
        {
            "id": "esp32_product_resources",
            "question": "ESP32 \u4ea7\u54c1\u9875\u63d0\u5230\u54ea\u4e9b\u8d44\u6e90\u5165\u53e3\uff1f",
            "expected_documents": ["ESP32 Product Documentation"],
            "expected_terms": ["Resources", "Documents", "SDK", "Hardware Design Guidelines"],
            "intent": "product_resources",
        },
        {
            "id": "vehicle_power_performance_indexes",
            "question": "\u6c7d\u8f66\u52a8\u529b\u6027\u80fd\u7528\u54ea\u4e9b\u6307\u6807\u8861\u91cf\uff1f",
            "expected_documents": pdf_docs,
            "expected_terms": ["\u6700\u9ad8\u8f66\u901f", "\u52a0\u901f", "\u722c\u5761"],
            "intent": "pdf_domain_qa",
        },
        {
            "id": "tire_coordinate_axes",
            "question": "\u8f6e\u80ce\u5750\u6807\u7cfb\u7684 x/y/z \u8f74\u5982\u4f55\u5b9a\u4e49\uff1f",
            "expected_documents": pdf_docs,
            "expected_terms": ["\u5750\u6807\u7cfb", "x", "y", "z"],
            "intent": "pdf_figure_text",
        },
        {
            "id": "rolling_resistance_factors",
            "question": "\u6eda\u52a8\u963b\u529b\u7cfb\u6570\u4e0e\u54ea\u4e9b\u56e0\u7d20\u6709\u5173\uff1f",
            "expected_documents": pdf_docs,
            "expected_terms": ["\u6eda\u52a8\u963b\u529b\u7cfb\u6570", "\u8def\u9762", "\u8f6e\u80ce", "\u8f66\u901f"],
            "intent": "pdf_table_text",
        },
    ]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = read_json("chunks.json")
    docs = read_json("documents.json")
    vectors = read_json("vectors.json")

    chunks_by_doc: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        chunks_by_doc[chunk["document_id"]].append(chunk)
    for doc_chunks in chunks_by_doc.values():
        doc_chunks.sort(key=lambda item: item["chunk_index"])

    lengths = [len(chunk.get("content", "")) for chunk in chunks]
    short_chunks = [chunk for chunk in chunks if len(chunk.get("content", "")) < 100]
    very_short_chunks = [chunk for chunk in chunks if len(chunk.get("content", "")) < 50]
    long_chunks = [chunk for chunk in chunks if len(chunk.get("content", "")) > 2000]
    formula_chunks = [chunk for chunk in chunks if chunk.get("block_type") == "formula"]
    formula_leakage_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("block_type") == "text" and looks_like_formula_leakage(chunk.get("content", ""))
    ]
    bad_start_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("block_type") == "text" and looks_like_bad_start(chunk.get("content", ""))
    ]
    chapter_transition_error_chunks = [
        chunk for chunk in chunks if chapter_transition_path_error(chunk.get("section_path") or [])
    ]
    heading_recall_samples = [
        (chunk, candidate)
        for chunk in chunks
        if chunk.get("document_title", "").startswith(VEHICLE_THEORY)
        for candidate in [candidate_heading_from_text(chunk.get("content", ""), chunk.get("section_path") or [])]
        if candidate
    ]

    examples: dict[str, list[dict]] = {}
    section_issue_counter: Counter[str] = Counter()
    section_issue_chunks: set[str] = set()
    for chunk in chunks:
        for part in chunk.get("section_path") or []:
            issue = section_issue(part)
            if issue:
                section_issue_counter[issue] += 1
                section_issue_chunks.add(chunk["id"])
                add_example(examples, f"section_path:{issue}", chunk, detail=part)

    for chunk in short_chunks:
        add_example(examples, "short_chunks_lt_100", chunk, detail=f"len={len(chunk.get('content', ''))}", limit=20)
    for chunk in formula_leakage_chunks:
        add_example(examples, "formula_leakage_in_text", chunk, detail=f"formula_score={pdf_formula_score(chunk.get('content', '')):.2f}", limit=12)
    for chunk in bad_start_chunks:
        add_example(examples, "bad_start_chunks", chunk, detail="starts like a continuation", limit=12)
    for chunk in chapter_transition_error_chunks:
        add_example(examples, "section_path:chapter_transition_error", chunk, detail=" > ".join(chunk.get("section_path") or []), limit=12)
    for chunk, candidate in heading_recall_samples:
        add_example(examples, "heading_recall_sample:medium_candidate_not_in_path", chunk, detail=candidate, limit=12)

    single_line_code = []
    short_code = []
    code_without_context = []
    for chunk in chunks:
        if chunk.get("block_type") != "code":
            continue
        content = chunk.get("content", "")
        code_lines = [line for line in content.splitlines() if line.strip()]
        if len(code_lines) == 1:
            single_line_code.append(chunk)
            add_example(examples, "single_line_code_chunks", chunk, detail=f"len={len(content)}", limit=20)
        if len(content) < 100:
            short_code.append(chunk)
        doc_chunks = chunks_by_doc[chunk["document_id"]]
        index = chunk["chunk_index"]
        prev_chunk = next((item for item in doc_chunks if item["chunk_index"] == index - 1), None)
        next_chunk = next((item for item in doc_chunks if item["chunk_index"] == index + 1), None)
        if (prev_chunk is None or prev_chunk.get("block_type") == "code") and (
            next_chunk is None or next_chunk.get("block_type") == "code"
        ):
            code_without_context.append(chunk)
            add_example(examples, "code_without_adjacent_text", chunk, detail="neighbor chunks are missing or code")

    table_issue_counter: Counter[str] = Counter()
    table_confidence_counter: Counter[str] = Counter()
    for chunk in chunks:
        if chunk.get("block_type") != "table":
            continue
        content = chunk.get("content", "")
        confidence = chunk.get("table_parse_confidence") or table_parse_confidence(content)
        table_confidence_counter[confidence] += 1
        if is_bad_table(content):
            table_issue_counter["bad_table_filter_match"] += 1
            add_example(examples, "table:bad_table_filter_match", chunk)
        rows = [line for line in content.splitlines() if "|" in line and not is_separator_row(line)]
        pipe_counts = [row.count("|") for row in rows]
        if len(set(pipe_counts)) > 2:
            table_issue_counter["inconsistent_column_count"] += 1
            add_example(examples, "table:inconsistent_column_count", chunk, detail=f"pipe_counts={pipe_counts[:10]}")
        packed_cells = []
        for row in rows:
            for cell in row.strip("|").split("|"):
                tokens = re.findall(r"[A-Za-z0-9.\-/\u4e00-\u9fff]+", cell)
                numeric = [token for token in tokens if re.search(r"\d", token)]
                if len(tokens) >= 8 and len(numeric) >= 4:
                    packed_cells.append(clean_one_line(cell, 120))
        if packed_cells:
            table_issue_counter["packed_multi_value_cells"] += 1
            add_example(examples, "table:packed_multi_value_cells", chunk, detail=" | ".join(packed_cells[:2]))

    product_allowed = {"ESP32", "ESP32 SoC", "Resources", "Products", "Buy Now", "Overview"}
    for chunk in chunks:
        if chunk.get("document_title") != "ESP32 Product Documentation":
            continue
        path = chunk.get("section_path") or []
        if not path:
            add_example(examples, "product_page:empty_section_path", chunk, detail="empty section_path")
        elif any(part not in product_allowed for part in path):
            add_example(examples, "product_page:unexpected_section_path", chunk, detail=" > ".join(path))

    pdf_chunks = [chunk for chunk in chunks if chunk.get("document_title", "").startswith(VEHICLE_THEORY)]
    pdf_section_issue_count = sum(1 for chunk in pdf_chunks if chunk["id"] in section_issue_chunks)
    pdf_title = pdf_chunks[0].get("document_title") if pdf_chunks else None
    smoke_questions = make_smoke_questions(pdf_title)

    lines = [
        "# Chunk Quality Report",
        "",
        f"- Generated at: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%SZ')}",
        f"- Documents: {len(docs)}",
        f"- Chunks: {len(chunks)}",
        f"- Vectors: {len(vectors)}",
    ]
    if lengths:
        lines.extend(
            [
                f"- Content length median: {median(lengths):.0f}",
                f"- Content length average: {mean(lengths):.1f}",
            ]
        )
    lines.extend(
        [
            f"- Short chunks (<100 chars): {len(short_chunks)}",
            f"- Very short chunks (<50 chars): {len(very_short_chunks)}",
            f"- Long chunks (>2000 chars): {len(long_chunks)}",
            f"- Formula chunks: {len(formula_chunks)}",
            f"- Formula leakage chunks: {len(formula_leakage_chunks)}",
            f"- Bad start chunks: {len(bad_start_chunks)}",
            f"- Block types: {dict(Counter(chunk.get('block_type', 'text') for chunk in chunks))}",
            f"- Table confidence: {dict(table_confidence_counter)}",
            "",
            "## Documents",
            "",
            "| Document | Source format | Chunks | Block types | Median len | Short <100 |",
            "|---|---:|---:|---|---:|---:|",
        ]
    )
    for doc in docs:
        doc_chunks = chunks_by_doc[doc["id"]]
        doc_lengths = [len(chunk.get("content", "")) for chunk in doc_chunks]
        block_counts = dict(Counter(chunk.get("block_type", "text") for chunk in doc_chunks))
        med = median(doc_lengths) if doc_lengths else 0
        short = sum(1 for chunk in doc_chunks if len(chunk.get("content", "")) < 100)
        lines.append(f"| {doc['title']} | {doc.get('source_format')} | {len(doc_chunks)} | `{block_counts}` | {med:.0f} | {short} |")

    lines.extend(
        [
            "",
            "## Issue Summary",
            "",
            f"- Section path issue chunks: {len(section_issue_chunks)}",
            f"- Path pollution rate: {(len(section_issue_chunks) / len(chunks) if chunks else 0):.4f}",
            f"- Section path issue parts: {dict(section_issue_counter)}",
            f"- PDF section path issue chunks: {pdf_section_issue_count} / {len(pdf_chunks)}",
            f"- Chapter transition path errors: {len(chapter_transition_error_chunks)}",
            f"- Heading recall sample candidates: {len(heading_recall_samples)}",
            f"- Formula chunks: {len(formula_chunks)}",
            f"- Formula leakage chunks: {len(formula_leakage_chunks)}",
            f"- Formula leakage rate: {(len(formula_leakage_chunks) / len(chunks) if chunks else 0):.4f}",
            f"- Bad start chunks: {len(bad_start_chunks)}",
            f"- Bad start rate: {(len(bad_start_chunks) / len(chunks) if chunks else 0):.4f}",
            f"- Table issue counts: {dict(table_issue_counter)}",
            f"- Table confidence distribution: {dict(table_confidence_counter)}",
            f"- Code chunks: {sum(1 for chunk in chunks if chunk.get('block_type') == 'code')}",
            f"- Single-line code chunks: {len(single_line_code)}",
            f"- Short code chunks (<100 chars): {len(short_code)}",
            f"- Code chunks without adjacent text context: {len(code_without_context)}",
            "",
            "## Priority Findings",
            "",
            "1. Track chapter-transition path errors separately; a path should not contain two chapter-level headings.",
            "2. Keep table chunks, but treat low-confidence packed multi-value tables as risky evidence instead of exact row/column data.",
            "3. Single-line command/code chunks are correctly typed as code, but small commands still need parent context for intent.",
            "4. Watch heading recall samples so stricter path cleaning does not silently drop real front-matter or section titles.",
            "",
        ]
    )

    for key in sorted(examples):
        lines.extend([f"## Examples: {key}", ""])
        for offset, item in enumerate(examples[key], start=1):
            lines.extend(
                [
                    f"### {offset}. {item['document_title']} / chunk {item['chunk_index']}",
                    "",
                    f"- block_type: `{item['block_type']}`",
                    f"- section_path: `{' > '.join(item['section_path'])}`",
                ]
            )
            if item.get("page_label"):
                lines.append(f"- page_label: `{item['page_label']}`")
            if item.get("location_label"):
                lines.append(f"- location_label: `{item['location_label']}`")
            if item.get("detail"):
                lines.append(f"- detail: `{item['detail']}`")
            lines.extend(["", "```text", item["snippet"], "```", ""])

    lines.extend(
        [
            "## RAG Smoke Test Questions",
            "",
            "The machine-readable version is saved as `rag_smoke_questions.json`. Suggested metrics: Hit@1, Hit@3, Hit@5, MRR, context precision, context recall, citation accuracy.",
            "",
        ]
    )
    for question in smoke_questions:
        lines.append(f"- `{question['id']}`: {question['question']}")

    report_path = REPORT_DIR / "chunk_quality_report.md"
    questions_path = REPORT_DIR / "rag_smoke_questions.json"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    questions_path.write_text(json.dumps(smoke_questions, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "documents": len(docs),
                "chunks": len(chunks),
                "vectors": len(vectors),
                "short_chunks_lt_100": len(short_chunks),
                "section_issue_chunks": len(section_issue_chunks),
                "pdf_section_issue_chunks": pdf_section_issue_count,
                "path_pollution_rate": len(section_issue_chunks) / len(chunks) if chunks else 0,
                "formula_chunks": len(formula_chunks),
                "formula_leakage_chunks": len(formula_leakage_chunks),
                "formula_leakage_rate": len(formula_leakage_chunks) / len(chunks) if chunks else 0,
                "chapter_transition_path_error_count": len(chapter_transition_error_chunks),
                "heading_recall_sample_count": len(heading_recall_samples),
                "bad_start_chunks": len(bad_start_chunks),
                "bad_start_rate": len(bad_start_chunks) / len(chunks) if chunks else 0,
                "table_issue_counts": dict(table_issue_counter),
                "table_confidence_distribution": dict(table_confidence_counter),
                "single_line_code_chunks": len(single_line_code),
                "report": str(report_path),
                "questions": str(questions_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
