import httpx
from openai import OpenAI

from app.config import Settings
from app.schemas import ChatTurn, Citation
from app.task_types import BOOK_INDEX, CODE_SYMBOL_LOOKUP, QA_EXPLANATION, TABLE_LOOKUP


class DeepSeekChatClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            http_client=httpx.Client(timeout=60.0, trust_env=False),
        )

    def answer(
        self,
        question: str,
        citations: list[Citation],
        history: list[ChatTurn],
        *,
        task_type: str | None = None,
    ) -> tuple[str, str | None]:
        context_blocks = []
        for citation in citations:
            location_parts = []
            if citation.section_path:
                location_parts.append(" > ".join(citation.section_path))
            if citation.page_label:
                location_parts.append(citation.page_label)
            if citation.location_label and citation.location_label not in location_parts:
                location_parts.append(citation.location_label)
            if citation.source_uri:
                location_parts.append(citation.source_uri)
            location = " | ".join(location_parts) if location_parts else f"片段 {citation.chunk_index}"
            context_blocks.append(
                (
                    f"[{citation.document_title} | {location}]"
                    f"\n{citation.content or citation.snippet}"
                )
            )

        recent_history = history[-self.settings.rag_max_history_messages :]
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个严谨的RAG问答助手。回答时必须优先依据给定资料，"
                    "不要编造来源中不存在的信息。若资料不足，请明确说不知道或资料不足。"
                    "回答尽量简洁；如果资料给出了章节、页码、行号、符号名或 URL 位置，请在答案里自然带出这些定位信息。"
                    f"{self._task_instruction(task_type)}"
                ),
            }
        ]
        messages.extend(turn.model_dump() for turn in recent_history)
        messages.append(
            {
                "role": "user",
                "content": (
                    "请基于下面检索到的资料回答问题。\n\n"
                    "资料：\n"
                    f"{'\n\n'.join(context_blocks) if context_blocks else '没有检索到相关资料。'}\n\n"
                    f"问题：{question}"
                ),
            }
        )

        extra_body = None
        if self.settings.deepseek_enable_thinking:
            extra_body = {"thinking": {"type": "enabled"}}

        request_payload = {
            "model": self.settings.deepseek_model,
            "messages": messages,
            "stream": False,
        }
        if extra_body is not None:
            request_payload["extra_body"] = extra_body

        response = self.client.chat.completions.create(**request_payload)
        message = response.choices[0].message
        answer = message.content or "暂时没有生成可用回答。"
        reasoning = getattr(message, "reasoning_content", None)
        return answer, reasoning

    @staticmethod
    def _task_instruction(task_type: str | None) -> str:
        if task_type == BOOK_INDEX:
            return " 如果用户在整理全书或章节索引，请优先按章节/主题结构化输出，并尽量附上页码或定位信息。"
        if task_type == TABLE_LOOKUP:
            return " 如果问题是表格或数值查找，请优先引用表格证据；当表格置信度低时，要明确说明该数值证据风险较高。"
        if task_type == CODE_SYMBOL_LOOKUP:
            return " 如果问题是代码定位，请优先回答符号名、文件、行号和相邻实现上下文。"
        if task_type == QA_EXPLANATION:
            return " 如果问题偏解释型，请先给结论，再用资料中的关键依据展开。"
        return ""
