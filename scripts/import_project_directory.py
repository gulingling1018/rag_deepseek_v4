#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.importers import (
    CODE_SUFFIXES,
    MARKDOWN_SUFFIXES,
    TEXT_SUFFIXES,
    WORD_SUFFIXES,
    extract_document_from_path,
)
from app.storage import JSONStorage


SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    "coverage",
    "data",
    "logs",
    "target",
}

SKIP_FILE_NAMES = {
    ".ds_store",
}


def iter_project_files(root: Path, include_hidden: bool) -> list[Path]:
    supported_suffixes = TEXT_SUFFIXES | MARKDOWN_SUFFIXES | WORD_SUFFIXES | CODE_SUFFIXES | {".pdf"}
    discovered: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.name.lower() in SKIP_FILE_NAMES:
            continue
        if not include_hidden and any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if any(part in SKIP_DIR_NAMES for part in path.relative_to(root).parts[:-1]):
            continue
        if path.suffix.lower() not in supported_suffixes:
            continue
        discovered.append(path)
    return sorted(discovered)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a local project directory into the RAG knowledge base.")
    parser.add_argument("directory", help="Project directory to import")
    parser.add_argument("--replace", action="store_true", help="Replace existing records for the same source path")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and directories")
    parser.add_argument("--max-files", type=int, default=0, help="Optional cap for imported files")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Directory not found: {root}")

    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    files = iter_project_files(root, include_hidden=args.include_hidden)
    if args.max_files > 0:
        files = files[: args.max_files]

    imported = 0
    skipped = 0
    failed = 0

    for path in files:
        existing = storage.find_document_by_source_path(str(path))
        if existing and not args.replace:
            print(f"skip existing: {path}")
            skipped += 1
            continue
        if existing and args.replace:
            storage.delete_document(existing.id)

        relative_name = path.relative_to(root).as_posix()
        try:
            extracted = extract_document_from_path(path)
            storage.add_document(
                filename=relative_name,
                source_path=str(path),
                text=extracted.text,
                title=relative_name,
                source_type="file",
                source_format=extracted.source_format,
                encoding=extracted.encoding,
                document_ir=extracted.document_ir,
                page_count=extracted.page_count,
            )
            imported += 1
            print(f"imported: {relative_name}")
        except Exception as exc:
            if "文档内容为空" in str(exc):
                skipped += 1
                print(f"skip empty: {relative_name}")
                continue
            failed += 1
            print(f"failed: {relative_name} -> {exc}")

    print(f"done: imported={imported}, skipped={skipped}, failed={failed}")


if __name__ == "__main__":
    main()
