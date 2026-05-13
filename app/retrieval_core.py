from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from hashlib import blake2b

from app.schemas import ChunkRecord

TECH_TERM_GROUPS = [
    {"bluetooth", "blue tooth", "bt", "蓝牙"},
    {"ble", "bluetooth le", "bluetooth low energy", "低功耗蓝牙", "蓝牙低能耗"},
    {"ble-only", "ble only", "only ble", "纯 ble", "纯ble", "只支持 ble", "仅支持 ble"},
    {"classic bluetooth", "classic bt", "br/edr", "经典蓝牙", "传统蓝牙"},
    {"host stack", "host api", "host apis", "host", "主机栈", "主机堆栈", "协议栈", "蓝牙主机"},
    {"nimble", "nimble host", "apache nimble"},
    {"bluedroid", "esp-bluedroid"},
    {"gatt", "generic attribute", "属性协议"},
    {"gap", "generic access", "接入规范"},
    {"advertising", "advertise", "广播"},
    {"scan", "scanning", "扫描"},
    {"pairing", "bonding", "配对", "绑定"},
    {"security", "smp", "安全"},
    {"service", "services", "服务"},
    {"characteristic", "characteristics", "特征", "特征值"},
    {"api", "apis", "接口"},
    {"guide", "guides", "programming guide", "development guide", "指南", "开发指南"},
    {"overview", "architecture", "概述", "架构"},
    {"example", "examples", "示例"},
    {"controller", "host", "控制器", "主机"},
    {"audio", "a2dp", "音频"},
    {"spp", "serial port profile"},
]


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("®", " ")
    return normalized


def stem_latin_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("es"):
        return token[:-2]
    if len(token) > 2 and token.endswith("s"):
        return token[:-1]
    return token


def latin_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_./+-]+", normalize_text(text))
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        expanded.append(stem_latin_token(token))
    return [token for token in expanded if token]


def cjk_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for seq in re.findall(r"[\u4e00-\u9fff]+", text):
        tokens.extend(list(seq))
        if len(seq) > 1:
            tokens.extend(seq[index : index + 2] for index in range(len(seq) - 1))
    return tokens


def phrase_expansions(text: str) -> list[str]:
    normalized = normalize_text(text)
    additions: set[str] = set()
    for group in TECH_TERM_GROUPS:
        if any(term in normalized or term in text for term in group):
            additions.update(group)
    return list(additions)


def tokenize(text: str) -> list[str]:
    expansions = " ".join(phrase_expansions(text))
    merged = f"{text}\n{expansions}" if expansions else text
    return latin_tokens(merged) + cjk_tokens(merged)


def document_metadata_tokens(chunk: ChunkRecord) -> str:
    parts = [
        chunk.doc_type.replace("_", " "),
        chunk.content_domain or "",
        chunk.chip_family or "",
        chunk.version or "",
        chunk.language or "",
        chunk.symbol_name or "",
    ]
    return " ".join(part for part in parts if part)


def build_weighted_chunk_text(chunk: ChunkRecord) -> str:
    section_text = " > ".join(chunk.section_path) if chunk.section_path else ""
    location_text = " ".join(
        part for part in [chunk.page_label, chunk.location_label, chunk.source_uri] if part
    )
    metadata_text = document_metadata_tokens(chunk)
    return (
        f"{chunk.document_title}\n{chunk.document_title}\n"
        f"{metadata_text}\n{section_text}\n{location_text}\n{chunk.content}"
    )


def l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0:
        return values
    return [value / norm for value in values]


def token_hash(token: str, salt: bytes) -> bytes:
    return blake2b(token.encode("utf-8"), digest_size=16, key=salt).digest()


def vectorize_tokens_hash(tokens: list[str], dimension: int) -> list[float]:
    values = [0.0] * dimension
    if dimension <= 0:
        return values

    counts = Counter(tokens)
    for token, count in counts.items():
        weight = 1.0 + math.log1p(count)
        for salt in (b"rag-v1-a", b"rag-v1-b"):
            digest = token_hash(token, salt)
            index = int.from_bytes(digest[:4], "big") % dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            values[index] += sign * weight
    return l2_normalize(values)


def vectorize_text_hash(text: str, dimension: int) -> list[float]:
    return vectorize_tokens_hash(tokenize(text), dimension)
