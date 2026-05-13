from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.task_types import BOOK_INDEX, CODE_SYMBOL_LOOKUP, QA_EXPLANATION, QA_FACT, TABLE_LOOKUP


@dataclass
class TaskPlan:
    task_type: str
    candidate_limit: int
    preferred_block_types: set[str] = field(default_factory=set)
    require_locations: bool = False
    require_page_numbers: bool = False
    prefer_code: bool = False
    prefer_symbol_lookup: bool = False
    prefer_tables: bool = False
    prefer_toc: bool = False
    answer_style: str = "direct"


class TaskRouter:
    def route(self, question: str, *, top_k: int) -> TaskPlan:
        normalized = re.sub(r"\s+", " ", question).strip().lower()

        if self._is_book_index_request(normalized):
            return TaskPlan(
                task_type=BOOK_INDEX,
                candidate_limit=max(top_k * 10, 40),
                preferred_block_types={"toc", "text"},
                require_locations=True,
                require_page_numbers=True,
                prefer_toc=True,
                answer_style="structured_index",
            )

        if self._is_table_lookup_request(normalized):
            return TaskPlan(
                task_type=TABLE_LOOKUP,
                candidate_limit=max(top_k * 8, 30),
                preferred_block_types={"table", "text"},
                require_locations=True,
                require_page_numbers=True,
                prefer_tables=True,
                answer_style="table_focused",
            )

        if self._is_code_symbol_request(question, normalized):
            return TaskPlan(
                task_type=CODE_SYMBOL_LOOKUP,
                candidate_limit=max(top_k * 8, 30),
                preferred_block_types={"code", "text"},
                require_locations=True,
                prefer_code=True,
                prefer_symbol_lookup=True,
                answer_style="code_focused",
            )

        if self._is_explanation_request(normalized):
            return TaskPlan(
                task_type=QA_EXPLANATION,
                candidate_limit=max(top_k * 8, 30),
                require_locations=False,
                answer_style="explanatory",
            )

        return TaskPlan(
            task_type=QA_FACT,
            candidate_limit=max(top_k * 8, 30),
            require_locations=False,
            answer_style="direct",
        )

    @staticmethod
    def _is_book_index_request(normalized: str) -> bool:
        terms = (
            "全书",
            "知识点索引",
            "索引",
            "章节索引",
            "按章整理",
            "按章节",
            "目录结构",
            "章节结构",
            "全书结构",
        )
        return any(term in normalized for term in terms)

    @staticmethod
    def _is_table_lookup_request(normalized: str) -> bool:
        terms = (
            "表格",
            "参数表",
            "数值",
            "对应值",
            "同比",
            "环比",
            "table",
            "coefficient",
            "value",
            "参数",
        )
        return any(term in normalized for term in terms)

    @staticmethod
    def _is_code_symbol_request(question: str, normalized: str) -> bool:
        code_terms = (
            "代码",
            "源码",
            "函数",
            "方法",
            "类",
            "模块",
            "定义",
            "调用",
            "symbol",
            "file",
            "文件",
            "目录",
        )
        if any(term in normalized for term in code_terms):
            return True
        identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", question)
        ignored = {"esp32", "bluetooth", "nimble", "bluedroid", "guide", "table", "code"}
        return any(
            (
                "_" in identifier
                or any(char.isupper() for char in identifier[1:])
            )
            and identifier.lower() not in ignored
            for identifier in identifiers
        )

    @staticmethod
    def _is_explanation_request(normalized: str) -> bool:
        terms = ("为什么", "原理", "解释", "总结", "概述", "说明", "how", "why")
        return any(term in normalized for term in terms)
