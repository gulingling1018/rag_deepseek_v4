import math
import re
from collections import Counter
from dataclasses import dataclass, field

from app.embeddings import EmbeddingService
from app.retrieval_core import build_weighted_chunk_text, normalize_text, tokenize
from app.schemas import ChatTurn, ChunkRecord, VectorRecord


def build_query_text(question: str, history: list[ChatTurn], window: int = 4) -> str:
    recent_user_turns = [turn.content for turn in history if turn.role == "user"][-window:]
    parts = recent_user_turns + [question]
    return "\n".join(part for part in parts if part.strip())


@dataclass
class QueryIntent:
    preferred_chip_families: set[str] = field(default_factory=set)
    preferred_doc_types: set[str] = field(default_factory=set)
    discouraged_doc_types: set[str] = field(default_factory=set)
    prefer_pdf: bool = False
    prefer_locations: bool = False
    prefer_examples: bool = False
    allow_entrypoints: bool = False
    explicit_doc_lookup: bool = False
    prefer_catalog: bool = False
    prefer_bluetooth: bool = False
    prefer_interactive_comm: bool = False
    prefer_code: bool = False
    prefer_project: bool = False
    prefer_build_config: bool = False
    prefer_symbol_lookup: bool = False
    identifier_hints: set[str] = field(default_factory=set)


def classify_query_intent(question: str) -> QueryIntent:
    normalized_question = normalize_text(question)
    intent = QueryIntent()
    identifier_candidates = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", question))
    ignored_identifiers = {"esp32", "ble", "bluetooth", "nimble", "bluedroid", "guide", "api", "code", "main"}
    intent.identifier_hints = {
        candidate for candidate in identifier_candidates
        if "_" in candidate or any(char.isupper() for char in candidate[1:]) or candidate.lower() not in ignored_identifiers
    }

    for chip in ("esp32c3", "esp32s3", "esp32s2", "esp32c6", "esp32h2", "esp32"):
        if chip in normalized_question:
            intent.preferred_chip_families.add(chip)

    if any(term in normalized_question for term in (".pdf", "datasheet", "trm", "手册", "规格书", "技术参考手册")):
        intent.prefer_pdf = True
        intent.explicit_doc_lookup = True
        intent.preferred_doc_types.update({"datasheet", "trm", "hardware_design", "schematic"})

    if any(term in normalized_question for term in ("页码", "第几页", "参数表", "表", "table", "寄存器", "电流", "电压", "功耗", "引脚", "封装")):
        intent.prefer_pdf = True
        intent.preferred_doc_types.update({"datasheet", "trm", "hardware_design"})

    if any(term in normalized_question for term in ("代码", "源码", "实现", "函数", "方法", "类", "模块", "组件", "文件", "目录", "main.c", "app_main", "cmakelists", "kconfig", "sdkconfig", "menuconfig", "示例代码", "example code")):
        intent.prefer_code = True
        intent.prefer_project = True
        intent.prefer_symbol_lookup = True
        intent.preferred_doc_types.update({"source_code", "build_config", "project_config", "project_doc"})
        intent.discouraged_doc_types.update({"datasheet", "trm", "product_catalog"})

    if any(term in normalized_question for term in ("sdkconfig", "menuconfig", "kconfig", "cmakelists", "组件依赖", "分区表配置", "构建脚本")):
        intent.prefer_build_config = True
        intent.prefer_code = True
        intent.preferred_doc_types.update({"build_config", "project_config", "guide"})

    if any(term in normalized_question for term in ("位置", "章节", "url", "链接", "哪一节", "哪个章节")):
        intent.prefer_locations = True
        intent.preferred_doc_types.update({"guide", "api_reference", "tooling", "security"})

    if any(term in normalized_question for term in ("怎么", "如何", "开发", "配置", "初始化", "api", "menuconfig", "示例", "教程", "快速入门", "guide")):
        intent.preferred_doc_types.update({"guide", "api_reference", "tooling", "security"})
        intent.discouraged_doc_types.update({"datasheet", "trm", "product_catalog"})

    if any(term in normalized_question for term in ("手机", "互发", "收发", "gatt", "gap", "notify", "write", "service", "characteristic", "特征", "服务", "blufi", "spp")):
        intent.prefer_examples = True
        intent.prefer_interactive_comm = True
        intent.preferred_doc_types.update({"guide", "api_reference"})
        intent.discouraged_doc_types.update({"datasheet", "trm", "product_catalog"})

    if any(term in normalized_question for term in ("蓝牙", "ble", "nimble", "bluedroid", "经典蓝牙", "br/edr")):
        intent.prefer_bluetooth = True
        intent.preferred_doc_types.update({"guide", "api_reference"})

    if any(term in normalized_question for term in ("总览", "入口", "文档页", "产品页", "选型", "系列资料", "catalog")):
        intent.prefer_catalog = True
        intent.allow_entrypoints = True
        intent.preferred_doc_types.update({"catalog", "product_catalog", "programming_guide_home", "hardware_reference_home", "index"})

    return intent


def heuristic_relevance_adjustment(question: str, chunk: ChunkRecord, intent: QueryIntent | None = None) -> float:
    normalized_question = normalize_text(question)
    lookup_text = normalize_text(build_weighted_chunk_text(chunk))
    title_text = normalize_text(chunk.document_title)
    intent = intent or classify_query_intent(question)
    adjustment = 0.0

    software_terms = ("主机栈", "主机堆栈", "协议栈", "host stack", "host api", "nimble", "bluedroid", "开发", "指南", "api")
    if any(term in question or term in normalized_question for term in software_terms):
        if any(term in lookup_text for term in ("nimble", "bluedroid", "host", "stack", "api reference", "programming sequence")):
            adjustment += 0.16
        if any(term in lookup_text for term in ("programming guide", "编程指南", "api", "menuconfig")):
            adjustment += 0.08
        if "datasheet" in title_text or "技术规格书" in lookup_text:
            adjustment -= 0.18

    ble_only_terms = ("只支持 ble", "仅支持 ble", "纯 ble", "纯ble", "ble-only", "ble only", "only ble")
    if any(term in question or term in normalized_question for term in ble_only_terms):
        if "nimble" in lookup_text:
            adjustment += 0.18
        if "bluedroid" in lookup_text and "classic" in lookup_text:
            adjustment -= 0.06

    classic_terms = ("经典蓝牙", "传统蓝牙", "br/edr", "classic bluetooth")
    if any(term in question or term in normalized_question for term in classic_terms):
        if "bluedroid" in lookup_text:
            adjustment += 0.16
        if "nimble" in lookup_text:
            adjustment -= 0.04

    if chunk.doc_type in intent.preferred_doc_types:
        adjustment += 0.18
    if chunk.doc_type in intent.discouraged_doc_types:
        adjustment -= 0.18

    if intent.prefer_code:
        if chunk.doc_type in {"source_code", "build_config", "project_config", "project_doc"}:
            adjustment += 0.24
        elif chunk.doc_type in {"guide", "api_reference"}:
            adjustment += 0.03
        else:
            adjustment -= 0.16

    if intent.prefer_project and chunk.content_domain == "project":
        adjustment += 0.18

    if not intent.prefer_code and chunk.content_domain == "project":
        adjustment -= 0.36

    if intent.prefer_build_config:
        config_terms = ("sdkconfig", "menuconfig", "kconfig", "cmakelists", "idf_component_register", "component", "partition", "config")
        if any(term in lookup_text for term in config_terms):
            adjustment += 0.18

    if intent.prefer_symbol_lookup:
        symbol_terms = ("app_main", "init", "start", "handler", "task", "callback", "config", "setup", "ble")
        if chunk.symbol_name:
            adjustment += 0.16
            if any(term in normalize_text(chunk.symbol_name) for term in symbol_terms):
                adjustment += 0.04
        elif chunk.block_type == "code":
            adjustment += 0.04
        if chunk.doc_type == "project_doc":
            adjustment -= 0.10

    if intent.identifier_hints:
        symbol_lookup = normalize_text(chunk.symbol_name or "")
        if any(identifier.lower() == symbol_lookup for identifier in intent.identifier_hints):
            adjustment += 0.42
        elif any(identifier.lower() in lookup_text for identifier in intent.identifier_hints):
            adjustment += 0.16
        elif chunk.doc_type in {"source_code", "build_config", "project_config"}:
            adjustment -= 0.06

    if intent.prefer_bluetooth:
        bluetooth_terms = ("bluetooth", "ble", "nimble", "bluedroid", "gatt", "gap", "spp", "a2dp", "蓝牙", "低功耗蓝牙", "经典蓝牙")
        if any(term in lookup_text for term in bluetooth_terms):
            adjustment += 0.20
        else:
            adjustment -= 0.46

    if chunk.chip_family and intent.preferred_chip_families:
        if chunk.chip_family in intent.preferred_chip_families:
            adjustment += 0.12
        else:
            adjustment -= 0.06

    if intent.prefer_pdf:
        if chunk.page_number is not None:
            adjustment += 0.12
        if chunk.doc_type in {"datasheet", "trm", "hardware_design", "schematic"}:
            adjustment += 0.14
        elif chunk.doc_type in {"programming_guide_home", "product_catalog", "catalog"}:
            adjustment -= 0.22

    if intent.prefer_locations:
        if chunk.source_uri or chunk.section_path:
            adjustment += 0.10
        if chunk.page_number is not None:
            adjustment += 0.04

    if intent.prefer_examples:
        example_terms = ("example", "examples", "示例", "教程", "gatt", "gap", "notify", "service", "characteristic", "write", "read")
        if any(term in lookup_text for term in example_terms):
            adjustment += 0.16
        if any(term in title_text for term in ("概述", "overview", "架构")) and "gatt" not in lookup_text:
            adjustment -= 0.08

    if intent.prefer_interactive_comm:
        comm_terms = ("gatt", "gap", "notify", "indicate", "read", "write", "service", "characteristic", "blufi", "spp", "扫描", "广播", "连接")
        if any(term in lookup_text for term in comm_terms):
            adjustment += 0.14
        else:
            adjustment -= 0.16

    if any(term in question or term in normalized_question for term in ("软件组件", "开发环境", "需要哪些软件", "what you need", "prerequisites")):
        if any(term in title_text or term in lookup_text for term in ("get started", "what you need", "toolchain", "python", "git")):
            adjustment += 0.70
        if "build system" in title_text or "component requirements" in lookup_text:
            adjustment -= 0.55
        if chunk.block_type == "code":
            adjustment -= 0.25

    if chunk.is_entrypoint and not intent.allow_entrypoints:
        adjustment -= 0.16
    if chunk.block_type == "formula":
        formula_terms = ("公式", "方程", "计算", "推导", "equation", "formula", "calculate", "derive")
        if any(term in question.lower() or term in normalized_question for term in formula_terms):
            adjustment += 0.08
        else:
            adjustment -= 0.24
    if chunk.block_type == "table" and chunk.table_parse_confidence == "low":
        exact_table_terms = ("数值", "系数", "效率", "对应", "table", "coefficient", "value", "efficiency")
        adjustment -= 0.10 if any(term in question.lower() or term in normalized_question for term in exact_table_terms) else 0.04
    adjustment += chunk.retrieval_priority * 0.03

    return adjustment

def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


class BM25Index:
    def __init__(self, chunks: list[ChunkRecord], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.term_frequencies: list[Counter[str]] = []
        self.doc_frequencies: Counter[str] = Counter()
        self.doc_lengths: list[int] = []
        self.avg_doc_length = 0.0

        for chunk in chunks:
            tokens = tokenize(build_weighted_chunk_text(chunk))
            counts = Counter(tokens)
            self.term_frequencies.append(counts)
            self.doc_lengths.append(len(tokens))
            for token in counts:
                self.doc_frequencies[token] += 1

        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

    def search(
        self,
        question: str,
        *,
        history: list[ChatTurn] | None = None,
        top_k: int = 5,
    ) -> list[tuple[ChunkRecord, float]]:
        if not self.chunks:
            return []

        query_text = build_query_text(question, history or [])
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return []

        total_docs = len(self.chunks)
        scored: list[tuple[int, float]] = []

        for index, counts in enumerate(self.term_frequencies):
            doc_len = self.doc_lengths[index] or 1
            score = 0.0

            for token in query_tokens:
                frequency = counts.get(token, 0)
                if frequency == 0:
                    continue

                doc_freq = self.doc_frequencies[token]
                idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                numerator = frequency * (self.k1 + 1)
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * doc_len / max(self.avg_doc_length, 1.0)
                )
                score += idf * numerator / denominator

            if score > 0:
                scored.append((index, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [(self.chunks[index], score) for index, score in scored[:top_k]]


class VectorIndex:
    def __init__(
        self,
        chunks: list[ChunkRecord],
        vectors: list[VectorRecord] | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self.chunks = chunks
        self.embedding_service = embedding_service
        self.spec = embedding_service.spec if embedding_service else None
        self.vector_map: dict[str, VectorRecord] = {}
        for item in vectors or []:
            if self.spec is None:
                self.vector_map[item.chunk_id] = item
                continue
            if (
                item.provider == self.spec.provider
                and item.model == self.spec.model
                and item.dimension == self.spec.dimension
            ):
                self.vector_map[item.chunk_id] = item

    def search(
        self,
        question: str,
        *,
        history: list[ChatTurn] | None = None,
        top_k: int = 5,
    ) -> list[tuple[ChunkRecord, float]]:
        if not self.chunks or self.embedding_service is None:
            return []

        query_text = build_query_text(question, history or [])
        try:
            query_vector = self.embedding_service.embed_query(query_text)
        except Exception:
            return []
        if not any(query_vector):
            return []

        scored: list[tuple[ChunkRecord, float]] = []
        for chunk in self.chunks:
            record = self.vector_map.get(chunk.id)
            if not record:
                continue
            vector = record.values
            score = cosine_similarity(query_vector, vector)
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]


class HybridIndex:
    def __init__(
        self,
        chunks: list[ChunkRecord],
        vectors: list[VectorRecord] | None = None,
        *,
        embedding_service: EmbeddingService | None = None,
        bm25_weight: float = 0.55,
        vector_weight: float = 0.45,
    ):
        self.chunks = chunks
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.bm25 = BM25Index(chunks)
        self.vector = VectorIndex(chunks, vectors=vectors, embedding_service=embedding_service)

    @staticmethod
    def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        max_score = max(scores.values())
        if max_score <= 0:
            return {}
        return {key: value / max_score for key, value in scores.items()}

    def search(
        self,
        question: str,
        *,
        history: list[ChatTurn] | None = None,
        top_k: int = 5,
    ) -> list[tuple[ChunkRecord, float]]:
        if not self.chunks:
            return []

        candidate_limit = max(top_k * 8, 30)
        bm25_results = self.bm25.search(question, history=history, top_k=candidate_limit)
        vector_results = self.vector.search(question, history=history, top_k=candidate_limit)

        chunk_map = {chunk.id: chunk for chunk in self.chunks}
        bm25_scores = self._normalize_scores({chunk.id: score for chunk, score in bm25_results})
        vector_scores = self._normalize_scores({chunk.id: score for chunk, score in vector_results})
        intent = classify_query_intent(question)

        combined_ids = set(bm25_scores) | set(vector_scores)
        scored: list[tuple[ChunkRecord, float]] = []
        for chunk_id in combined_ids:
            score = (
                bm25_scores.get(chunk_id, 0.0) * self.bm25_weight
                + vector_scores.get(chunk_id, 0.0) * self.vector_weight
            )
            score += heuristic_relevance_adjustment(question, chunk_map[chunk_id], intent)
            if score > 0:
                scored.append((chunk_map[chunk_id], score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
