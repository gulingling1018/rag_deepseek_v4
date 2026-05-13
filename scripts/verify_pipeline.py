#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app, build_citations, storage  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def main() -> None:
    client = TestClient(app)
    created_document_ids: list[str] = []
    created_session_ids: list[str] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="rag_pipeline_"))

    try:
        health = client.get("/health")
        assert_true(health.status_code == 200, "健康检查失败。")

        markdown_path = tmpdir / "ble_notes.md"
        markdown_path.write_text(
            "# BLE Guide\n\n## Host Stack\n纯 BLE 项目优先选择 NimBLE，它是 BLE-only host stack。\n",
            encoding="utf-8",
        )
        code_path = tmpdir / "ble_demo.c"
        code_path.write_text(
            "\n".join(
                [
                    "#include <stdio.h>",
                    "",
                    "static void ble_start(void) {",
                    '    printf("ble start\\n");',
                    "}",
                    "",
                    "int main(void) {",
                    "    ble_start();",
                    "    return 0;",
                    "}",
                ]
            ),
            encoding="utf-8",
        )
        text_path = tmpdir / "cn_gbk.txt"
        text_path.write_bytes("中文编码测试\nBluetooth LE host stack\n".encode("gb18030"))

        for path in (markdown_path, code_path, text_path):
            with path.open("rb") as handle:
                response = client.post(
                    "/api/documents/upload",
                    files={"file": (path.name, handle.read(), "application/octet-stream")},
                )
            assert_true(response.status_code == 200, f"上传失败: {path.name} -> {response.text}")
            payload = response.json()["document"]
            created_document_ids.append(payload["id"])

        documents = {item.id: item for item in storage.list_documents()}
        chunks = storage.list_chunks()
        vectors = storage.list_vectors()
        chunk_map: dict[str, list] = {}
        for chunk in chunks:
            chunk_map.setdefault(chunk.document_id, []).append(chunk)

        assert_true(len(vectors) == len(chunks), "向量索引数量与 chunk 数量不一致。")

        markdown_doc = documents[created_document_ids[0]]
        code_doc = documents[created_document_ids[1]]
        text_doc = documents[created_document_ids[2]]

        assert_true(markdown_doc.source_format == "markdown", "Markdown 文档格式识别失败。")
        assert_true(code_doc.source_format == "code", "代码文档格式识别失败。")
        assert_true(text_doc.source_format == "text", "文本格式识别失败。")
        assert_true(
            (text_doc.encoding or "").lower() in {"gb18030", "gbk", "gb2312"},
            f"编码识别异常: {text_doc.encoding}",
        )

        markdown_chunks = chunk_map[markdown_doc.id]
        code_chunks = chunk_map[code_doc.id]
        text_chunks = chunk_map[text_doc.id]

        assert_true(
            any(chunk.line_start is not None and chunk.section_path for chunk in markdown_chunks),
            "Markdown chunk 未保留章节或行号信息。",
        )
        assert_true(
            any(chunk.line_start is not None and any("ble_start" in part for part in chunk.section_path) for chunk in code_chunks),
            "代码 chunk 未保留函数或行号信息。",
        )
        assert_true(
            any("中文编码测试" in chunk.content for chunk in text_chunks),
            "编码转换后文本内容异常。",
        )

        pdf_doc = next((item for item in documents.values() if item.filename == "esp32_datasheet_cn.pdf"), None)
        assert_true(pdf_doc is not None, "未找到已导入的 PDF 数据手册。")
        pdf_chunks = chunk_map[pdf_doc.id]
        assert_true(
            any(chunk.page_number is not None and chunk.page_label for chunk in pdf_chunks),
            "PDF chunk 未保留页码元数据。",
        )
        assert_true(
            any(chunk.block_type == "table" and chunk.page_number is not None for chunk in pdf_chunks),
            "PDF 表格块未正确入库。",
        )

        citations = build_citations(
            "我想做一个只支持 BLE 的 ESP32 项目，应该优先选哪个蓝牙主机栈？",
            history=[],
            top_k=5,
        )
        assert_true(citations, "中文问题没有检索到任何资料。")
        assert_true(
            any(
                "nimble" in citation.document_title.lower()
                or "nimble" in (citation.source_uri or "").lower()
                or "蓝牙 api" in citation.document_title.lower()
                for citation in citations
            ),
            "中文问题未可靠命中英文蓝牙文档。",
        )

        chat_response = client.post(
            "/api/chat",
            json={
                "question": "我想做一个只支持 BLE 的 ESP32 项目，应该优先选哪个蓝牙主机栈？请用中文回答并给出依据。",
                "top_k": 5,
            },
        )
        assert_true(chat_response.status_code == 200, f"问答链路失败: {chat_response.text}")
        chat_payload = chat_response.json()
        created_session_ids.append(chat_payload["session_id"])
        assert_true(chat_payload["citations"], "LLM 问答未返回引用。")
        assert_true(contains_chinese(chat_payload["answer"]), "LLM 未返回中文回答。")
        assert_true(
            any(
                "nimble" in citation["document_title"].lower()
                or "nimble" in (citation.get("source_uri") or "").lower()
                or "蓝牙 api" in citation["document_title"].lower()
                for citation in chat_payload["citations"]
            ),
            "中文问答未可靠引用英文蓝牙资料。",
        )

        print(
            json.dumps(
                {
                    "status": "ok",
                    "uploaded_documents": len(created_document_ids),
                    "chunk_count": len(chunks),
                    "vector_count": len(vectors),
                    "chat_session_id": chat_payload["session_id"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        for session_id in created_session_ids:
            client.delete(f"/api/sessions/{session_id}")
        for document_id in created_document_ids:
            client.delete(f"/api/documents/{document_id}")
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
