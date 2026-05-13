from __future__ import annotations

import re
import unicodedata


CODE_SECTION_MARKERS = (
    "idf_component_register",
    "target_link_libraries",
    "add_custom_command",
    "externalproject_add",
    "set_target_properties",
    "add_dependencies",
    "target_include_directories",
    "target_compile_options",
    "target_compile_definitions",
    "cmake_minimum_required",
    "project(",
    "${",
    "#include",
)

BAD_TABLE_MARKERS = (
    "Col1",
    "Col2",
    "Col3",
    "Col4",
    "Col5",
    "|||||",
)

CHINESE_NUMERAL = "\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u96f60-9"


def section_heading_level(title: str) -> int | None:
    cleaned = compact_ws(title)
    if not cleaned:
        return None
    if re.match(fr"^\u7b2c\s*[{CHINESE_NUMERAL}]+\s*\u7ae0\b", cleaned):
        return 1
    if re.match(fr"^\u7b2c\s*[{CHINESE_NUMERAL}]+\s*\u8282\b", cleaned):
        return 2
    if re.match(fr"^\u7b2c\s*[{CHINESE_NUMERAL}]+\s*\u7248\s*\u524d\u8a00$", cleaned):
        return 1
    if cleaned in {"\u5e8f", "\u524d\u8a00", "\u7eea\u8bba"}:
        return 1
    match = re.match(r"^(\d+(?:\.\d+)*)\s+\S+", cleaned)
    if match:
        return min(len(match.group(1).split(".")), 6)
    if re.match(r"^chapter\s+\d+\b", cleaned, flags=re.IGNORECASE):
        return 1
    if re.match(r"^section\s+\d+\b", cleaned, flags=re.IGNORECASE):
        return 2
    return None


def compact_ws(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text))
    return re.sub(r"\s+", " ", normalized).strip()


def valid_section_title(title: str) -> bool:
    cleaned = compact_ws(re.sub(r"[*`#]+", "", title))
    if not cleaned:
        return False
    if len(cleaned) > 80:
        return False
    if "|" in cleaned or "\t" in cleaned:
        return False

    lowered = cleaned.lower()
    if any(marker in lowered for marker in CODE_SECTION_MARKERS):
        return False
    if re.search(r"\b(?:srcs|include_dirs|requires|priv_requires)\b", lowered):
        return False
    if re.search(r"\b(?:if|for|while|switch|return)\s*\(", lowered):
        return False
    if re.search(r"^\s*(?:\$?\{?[\w./+-]+\}?=|[A-Za-z_][\w:.-]*\()", cleaned):
        return False
    if re.search(r"[{};]", cleaned) and not re.match(r"^\d+(?:\.\d+)*\s+", cleaned):
        return False
    if re.fullmatch(r"[-=:_./\\\d\s]+", cleaned):
        return False
    return True


def clean_section_path(section_path: object) -> list[str]:
    if not isinstance(section_path, list):
        return []

    cleaned_path: list[str] = []
    for item in section_path:
        cleaned = compact_ws(re.sub(r"[*`#]+", "", str(item)))
        if not valid_section_title(cleaned):
            continue
        level = section_heading_level(cleaned)
        if level == 1:
            prefix = []
            for existing in cleaned_path:
                if section_heading_level(existing) is None:
                    prefix.append(existing)
                    break
                break
            cleaned_path = prefix + [cleaned]
            continue
        if level is not None:
            prefix: list[str] = []
            for existing in cleaned_path:
                existing_level = section_heading_level(existing)
                if existing_level is None:
                    prefix.append(existing)
                elif existing_level < level:
                    prefix.append(existing)
            cleaned_path = prefix + [cleaned]
            continue
        if cleaned not in cleaned_path:
            cleaned_path.append(cleaned)
    return cleaned_path


def table_parse_confidence(text: str) -> str:
    if is_bad_table(text):
        return "low"

    table_lines = [line.strip() for line in text.splitlines() if "|" in line]
    data_lines = [
        line
        for line in table_lines
        if not re.fullmatch(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?", line)
    ]
    if len(data_lines) < 2:
        return "low"

    pipe_counts = [line.count("|") for line in data_lines]
    if len(set(pipe_counts)) > 2:
        return "low"

    packed_cells = 0
    for row in data_lines:
        for cell in row.strip("|").split("|"):
            tokens = re.findall(r"[A-Za-z0-9.\-/\u4e00-\u9fff]+", cell)
            numeric = [token for token in tokens if re.search(r"\d", token)]
            if len(tokens) >= 8 and len(numeric) >= 4:
                packed_cells += 1

    if packed_cells:
        return "low"
    if len(data_lines) >= 3 and len(set(pipe_counts)) == 1:
        return "high"
    return "medium"


def is_bad_table(text: str) -> bool:
    if not text or "|" not in text:
        return False
    if any(marker in text for marker in BAD_TABLE_MARKERS):
        return True

    table_lines = [line.strip() for line in text.splitlines() if "|" in line]
    if not table_lines:
        return False

    pipe_count = text.count("|")
    tokens = re.findall(r"[\w\u4e00-\u9fff.+/-]+", text)
    unique_tokens = set(tokens)
    if pipe_count > 20 and len(unique_tokens) < 20:
        return True

    cells: list[str] = []
    for line in table_lines:
        if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?", line):
            continue
        cells.extend(cell.strip() for cell in line.strip("|").split("|"))

    if not cells:
        return True

    nonempty_cells = [cell for cell in cells if cell]
    if len(cells) >= 12 and len(nonempty_cells) / len(cells) < 0.35:
        return True

    alpha_tokens = [token for token in tokens if re.search(r"[A-Za-z\u4e00-\u9fff]", token)]
    digit_tokens = [token for token in tokens if re.fullmatch(r"\d+(?:\.\d+)?", token)]
    if pipe_count > 12 and len(alpha_tokens) <= 3 and len(digit_tokens) >= 8:
        return True

    return False
