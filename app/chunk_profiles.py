from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from app.document_ir import DocumentIR

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "general": {
        "profile_id": "general",
        "source_formats": [],
        "title_keywords": [],
        "chunk_strategy": "generic_text",
    },
    "source_code": {
        "profile_id": "source_code",
        "source_formats": ["code"],
        "title_keywords": [],
        "chunk_strategy": "source_code",
    },
    "markdown_guide": {
        "profile_id": "markdown_guide",
        "source_formats": ["markdown"],
        "title_keywords": [],
        "chunk_strategy": "markdown_guide",
    },
    "web_article": {
        "profile_id": "web_article",
        "source_formats": ["web"],
        "title_keywords": [],
        "chunk_strategy": "web_article",
    },
    "pdf_document": {
        "profile_id": "pdf_document",
        "source_formats": ["pdf", "pdf+ocr", "pdf+pymupdf4llm"],
        "title_keywords": [],
        "chunk_strategy": "pdf_document",
    },
}


def normalize_profile_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def merge_profile(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(override)
    return merged


@lru_cache(maxsize=1)
def load_chunk_profiles() -> dict[str, dict[str, Any]]:
    profiles = {profile_id: dict(payload) for profile_id, payload in BUILTIN_PROFILES.items()}
    if yaml is None or not PROFILE_DIR.exists():
        return profiles

    for path in sorted(PROFILE_DIR.glob("*.yaml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            continue
        profile_id = str(loaded.get("profile_id") or path.stem)
        base = profiles.get(profile_id, {})
        profiles[profile_id] = merge_profile(base, loaded)
    return profiles


def resolve_chunk_profile(
    document_ir: DocumentIR,
    *,
    filename: str,
    title: str | None,
    source_path: str,
    source_url: str | None,
) -> dict[str, Any]:
    profiles = load_chunk_profiles()
    resolved_title = title or document_ir.title or filename
    merged = " ".join(
        normalize_profile_text(value)
        for value in (filename, resolved_title, source_path, source_url, document_ir.source_format)
        if value
    )
    source_format = normalize_profile_text(document_ir.source_format)

    best_profile: dict[str, Any] | None = None
    best_score = -1
    for profile_id, profile in profiles.items():
        if profile_id == "general":
            continue

        source_formats = [normalize_profile_text(item) for item in profile.get("source_formats", [])]
        title_keywords = [normalize_profile_text(item) for item in profile.get("title_keywords", [])]
        if source_formats and source_format not in source_formats:
            continue
        matched_keywords = [keyword for keyword in title_keywords if keyword and keyword in merged]
        if title_keywords and not matched_keywords:
            continue

        score = 0
        if source_formats:
            score += 1
        score += len(matched_keywords) * 10
        if score > best_score:
            best_profile = profile
            best_score = score

    if best_profile is not None:
        return best_profile

    if source_format == "code":
        return profiles["source_code"]
    if source_format == "markdown":
        return profiles["markdown_guide"]
    if source_format == "web":
        return profiles["web_article"]
    if source_format.startswith("pdf"):
        return profiles["pdf_document"]
    return profiles["general"]
