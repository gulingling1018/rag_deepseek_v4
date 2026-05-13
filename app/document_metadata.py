from __future__ import annotations

from pathlib import Path
import re
import unicodedata


CHIP_FAMILIES = (
    "esp32p4",
    "esp32c61",
    "esp32c6",
    "esp32c5",
    "esp32c3",
    "esp32c2",
    "esp32h4",
    "esp32h2",
    "esp32s3",
    "esp32s2",
    "esp32",
    "esp8266",
)


def normalize_lookup(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").strip().lower()
    normalized = normalized.replace("\\", "/")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def strip_timestamp_prefix(name: str) -> str:
    return re.sub(r"^\d{14}_", "", name)


def trim_extension(name: str) -> str:
    return re.sub(r"\.[a-z0-9]+$", "", name, flags=re.IGNORECASE)


def build_lookup_variants(*values: str | None) -> set[str]:
    variants: set[str] = set()
    for value in values:
        if not value:
            continue
        normalized = normalize_lookup(value)
        if not normalized:
            continue

        basename = normalize_lookup(Path(normalized).name)
        candidates = {
            normalized,
            basename,
            strip_timestamp_prefix(normalized),
            strip_timestamp_prefix(basename),
        }
        for candidate in list(candidates):
            candidates.add(trim_extension(candidate))
            candidates.add(trim_extension(strip_timestamp_prefix(candidate)))

        variants.update(item for item in candidates if item)
    return variants


def detect_chip_family(*values: str | None) -> str | None:
    merged = " ".join(normalize_lookup(value) for value in values if value)
    for chip in CHIP_FAMILIES:
        if chip in merged:
            return chip
    return None


def detect_language(*values: str | None) -> str | None:
    merged = " ".join(value or "" for value in values)
    if "zh_cn" in merged.lower() or "中文" in merged:
        return "zh-CN"
    if re.search(r"[\u4e00-\u9fff]", merged):
        return "zh-CN"
    if any(token in merged.lower() for token in ("_en.", "/en/", "[english]", "english")):
        return "en"
    return None


def detect_version(*values: str | None) -> str | None:
    merged = " ".join(normalize_lookup(value) for value in values if value)
    match = re.search(r"\bv\d+(?:\.\d+){1,2}\b", merged)
    if match:
        return match.group(0)
    if "stable" in merged:
        return "stable"
    if "latest" in merged:
        return "latest"
    return None


def derive_document_metadata(
    *,
    filename: str,
    title: str,
    source_path: str,
    source_url: str | None,
    source_format: str | None,
    chunk_count: int,
) -> dict[str, str | int | bool | None]:
    lookup_values = [filename, title, source_path, source_url or "", source_format or ""]
    merged = " ".join(normalize_lookup(value) for value in lookup_values if value)
    normalized_title = normalize_lookup(title)
    normalized_filename = normalize_lookup(filename)
    basename = normalize_lookup(Path(filename).name)
    suffix = Path(filename).suffix.lower()

    chip_family = detect_chip_family(*lookup_values)
    language = detect_language(*lookup_values)
    version = detect_version(*lookup_values)

    doc_type = "other"
    content_domain = "general"
    is_entrypoint = False
    retrieval_priority = 0

    if "datasheet" in merged or "技术规格书" in merged:
        doc_type = "datasheet"
        content_domain = "hardware"
        retrieval_priority = 2
    elif "technical reference manual" in merged or "技术参考手册" in merged:
        doc_type = "trm"
        content_domain = "hardware"
        retrieval_priority = 2
    elif "hardware design guidelines" in merged or "硬件设计指南" in merged:
        doc_type = "hardware_design"
        content_domain = "hardware"
        retrieval_priority = 2
    elif "/security/" in merged or "flash 加密" in merged or "安全概述" in merged:
        doc_type = "security"
        content_domain = "software"
        retrieval_priority = 1
    elif source_format == "code":
        doc_type = "source_code"
        content_domain = "project"
        retrieval_priority = 2
    elif basename in {"cmakelists.txt", "kconfig", "kconfig.projbuild", "sdkconfig", "sdkconfig.defaults"}:
        doc_type = "build_config"
        content_domain = "project"
        retrieval_priority = 2
    elif normalized_filename.endswith((".yaml", ".yml", ".json", ".toml", ".ini")) and source_format in {"code", "text"}:
        doc_type = "project_config"
        content_domain = "project"
        retrieval_priority = 1
    elif normalized_filename.endswith((".md", ".markdown", ".mdx")) and any(token in merged for token in ("readme", "design", "architecture", "spec", "方案", "设计", "架构")):
        doc_type = "project_doc"
        content_domain = "project"
        retrieval_priority = 1
    elif "/api-reference/" in merged or " api " in f" {merged} ":
        doc_type = "api_reference"
        content_domain = "software"
        retrieval_priority = 1
    elif "/api-guides/" in merged or any(term in merged for term in ("快速入门", "构建系统", "idf.py", "ota 升级", "非易失性存储")):
        doc_type = "guide"
        content_domain = "software"
        retrieval_priority = 1
    elif "esptool" in merged or "vs code 扩展" in merged:
        doc_type = "tooling"
        content_domain = "tooling"
        retrieval_priority = 1
    elif "devkit" in merged or merged.endswith("_sch.pdf") or "schematic" in merged:
        doc_type = "schematic"
        content_domain = "hardware"
    elif "产品文档页" in merged or "/products/socs/" in merged:
        doc_type = "product_catalog"
        content_domain = "catalog"
        is_entrypoint = True
        retrieval_priority = -3
    elif "资料导入总览" in merged or "catalog" in Path(filename).stem.lower():
        doc_type = "catalog"
        content_domain = "catalog"
        is_entrypoint = True
        retrieval_priority = -2

    if doc_type == "other":
        if re.search(r"^esp-idf 编程指南 - esp32(?:-[a-z0-9]+)?$", normalized_title):
            doc_type = "programming_guide_home"
            content_domain = "software"
            is_entrypoint = True
            retrieval_priority = -2
        elif normalized_title.endswith("硬件参考"):
            doc_type = "hardware_reference_home"
            content_domain = "hardware"
            is_entrypoint = True
            retrieval_priority = -2
        elif "文档入口" in normalized_title:
            doc_type = "index"
            content_domain = "catalog"
            is_entrypoint = True
            retrieval_priority = -2

    if chunk_count <= 2 and doc_type in {"programming_guide_home", "hardware_reference_home", "index"}:
        is_entrypoint = True
        retrieval_priority = min(retrieval_priority, -2)

    return {
        "doc_type": doc_type,
        "content_domain": content_domain,
        "chip_family": chip_family,
        "version": version,
        "language": language,
        "is_entrypoint": is_entrypoint,
        "retrieval_priority": retrieval_priority,
    }
