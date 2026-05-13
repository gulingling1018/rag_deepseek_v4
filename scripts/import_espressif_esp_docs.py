#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sys
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.importers import extract_document_from_path, extract_web_document
from app.storage import JSONStorage


@dataclass(frozen=True)
class SourceRecord:
    category: str
    title: str
    url: str
    description: str
    kind: str = "web"
    filename: str | None = None


WEB_SOURCES: list[SourceRecord] = [
    SourceRecord(
        category="开发总览",
        title="ESP-IDF 编程指南 - ESP32",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/index.html",
        description="ESP32 目标的官方开发框架入口页，适合作为通用导航。",
    ),
    SourceRecord(
        category="开发总览",
        title="快速入门 - ESP32",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/get-started/index.html",
        description="环境搭建、示例编译、烧录与串口监视的起点文档。",
    ),
    SourceRecord(
        category="开发总览",
        title="idf.py 工具指南",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/tools/idf-py.html",
        description="覆盖构建、烧录、监视、菜单配置等常用开发命令。",
    ),
    SourceRecord(
        category="开发总览",
        title="构建系统 - ESP-IDF",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/build-system.html",
        description="组件组织、CMake、依赖与项目结构的核心说明。",
    ),
    SourceRecord(
        category="系统与存储",
        title="分区表",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/partition-tables.html",
        description="解释工厂分区、OTA 分区、NVS、文件系统等布局。",
    ),
    SourceRecord(
        category="系统与存储",
        title="NVS 非易失性存储",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/storage/nvs_flash.html",
        description="保存配置、配网信息、校准数据时的常用官方方案。",
    ),
    SourceRecord(
        category="系统与存储",
        title="OTA 升级",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/system/ota.html",
        description="应用在线升级、回滚与镜像切换的基础文档。",
    ),
    SourceRecord(
        category="安全",
        title="安全概述",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/security/security.html",
        description="量产安全设计入口，覆盖安全启动、Flash 加密等主题。",
    ),
    SourceRecord(
        category="安全",
        title="Flash 加密",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/security/flash-encryption.html",
        description="保护固件与敏感数据时最常查询的安全能力说明。",
    ),
    SourceRecord(
        category="无线连接",
        title="蓝牙架构概述",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/bt-architecture/overview.html",
        description="介绍控制器、主机栈以及 BLE/经典蓝牙关系。",
    ),
    SourceRecord(
        category="无线连接",
        title="低功耗蓝牙",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/ble/index.html",
        description="BLE 能力、限制与常见开发入口。",
    ),
    SourceRecord(
        category="无线连接",
        title="蓝牙 API",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/bluetooth/index.html",
        description="蓝牙 API 参考页，适合检索函数与组件定位。",
    ),
    SourceRecord(
        category="外设与系统",
        title="GPIO API",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/peripherals/gpio.html",
        description="最常用外设之一，适合查询中断、上下拉、模式配置。",
    ),
    SourceRecord(
        category="外设与系统",
        title="UART API",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/peripherals/uart.html",
        description="串口驱动、下载日志、AT/透传类应用经常会查到。",
    ),
    SourceRecord(
        category="外设与系统",
        title="ESP-IDF FreeRTOS",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-reference/system/freertos_idf.html",
        description="任务、队列、同步与 ESP-IDF FreeRTOS 差异说明。",
    ),
    SourceRecord(
        category="芯片导航",
        title="ESP32 硬件参考",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/hw-reference/index.html",
        description="ESP32 芯片、模组、开发板与硬件资源入口。",
    ),
    SourceRecord(
        category="芯片导航",
        title="ESP32-S3 硬件参考",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32s3/hw-reference/index.html",
        description="ESP32-S3 目标开发时的硬件入口页。",
    ),
    SourceRecord(
        category="芯片导航",
        title="ESP32-C3 硬件参考",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32c3/hw-reference/index.html",
        description="ESP32-C3 目标开发时的硬件入口页。",
    ),
    SourceRecord(
        category="芯片导航",
        title="ESP-IDF 编程指南 - ESP32-S3",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32s3/index.html",
        description="S3 目标的 IDF 文档入口，适合 USB、AI 指令等问题。",
    ),
    SourceRecord(
        category="芯片导航",
        title="ESP-IDF 编程指南 - ESP32-C3",
        url="https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32c3/index.html",
        description="C3 目标的 IDF 文档入口，适合 RISC-V 与 BLE 场景。",
    ),
    SourceRecord(
        category="工具链",
        title="esptool 文档入口",
        url="https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/index.html",
        description="串口下载、读写 flash、镜像操作等工具总览。",
    ),
    SourceRecord(
        category="工具链",
        title="esptool 基本命令",
        url="https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html",
        description="最常见的擦写、合并镜像、读写 flash 命令说明。",
    ),
    SourceRecord(
        category="工具链",
        title="ESP-IDF VS Code 扩展",
        url="https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/",
        description="使用 VS Code 进行配置、构建、调试时的官方说明。",
    ),
    SourceRecord(
        category="产品资料",
        title="ESP32 产品文档页",
        url="https://www.espressif.com/en/products/socs/esp32/documentation",
        description="ESP32 SoC 产品资源汇总页，包含文档、SDK、支持资源。",
    ),
    SourceRecord(
        category="产品资料",
        title="ESP32-S3 产品文档页",
        url="https://www.espressif.com/en/products/socs/esp32-s3/documentation",
        description="ESP32-S3 SoC 产品资源汇总页。",
    ),
    SourceRecord(
        category="产品资料",
        title="ESP32-C3 产品文档页",
        url="https://www.espressif.com/en/products/socs/esp32-c3/documentation",
        description="ESP32-C3 SoC 产品资源汇总页。",
    ),
]


PDF_SOURCES: list[SourceRecord] = [
    SourceRecord(
        category="芯片手册",
        title="ESP32 Datasheet",
        url="https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf",
        description="ESP32 规格书，适合查询引脚、电气、启动模式与资源参数。",
        kind="pdf",
        filename="esp32_datasheet_en.pdf",
    ),
    SourceRecord(
        category="芯片手册",
        title="ESP32 Technical Reference Manual",
        url="https://www.espressif.com/sites/default/files/documentation/esp32_technical_reference_manual_en.pdf",
        description="ESP32 低层外设、寄存器、时钟和内存架构参考手册。",
        kind="pdf",
        filename="esp32_technical_reference_manual_en.pdf",
    ),
    SourceRecord(
        category="硬件设计",
        title="ESP32 Hardware Design Guidelines",
        url="https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/esp-hardware-design-guidelines-en-master-esp32.pdf",
        description="ESP32 原理图、供电、下载电路、射频与 PCB 设计建议。",
        kind="pdf",
        filename="esp32_hardware_design_guidelines_en.pdf",
    ),
    SourceRecord(
        category="芯片手册",
        title="ESP32-S3 Datasheet",
        url="https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf",
        description="ESP32-S3 规格书，适合查询 USB、向量指令、引脚等参数。",
        kind="pdf",
        filename="esp32-s3_datasheet_en.pdf",
    ),
    SourceRecord(
        category="芯片手册",
        title="ESP32-S3 Technical Reference Manual",
        url="https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf",
        description="ESP32-S3 底层外设与寄存器手册。",
        kind="pdf",
        filename="esp32-s3_technical_reference_manual_en.pdf",
    ),
    SourceRecord(
        category="硬件设计",
        title="ESP32-S3 Hardware Design Guidelines",
        url="https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf",
        description="ESP32-S3 硬件设计、供电、下载和 PCB 约束说明。",
        kind="pdf",
        filename="esp32-s3_hardware_design_guidelines_en.pdf",
    ),
    SourceRecord(
        category="芯片手册",
        title="ESP32-C3 Datasheet",
        url="https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf",
        description="ESP32-C3 规格书，适合 BLE、RISC-V、引脚与功耗查询。",
        kind="pdf",
        filename="esp32-c3_datasheet_en.pdf",
    ),
    SourceRecord(
        category="芯片手册",
        title="ESP32-C3 Technical Reference Manual",
        url="https://www.espressif.com/sites/default/files/documentation/esp32-c3_technical_reference_manual_en.pdf",
        description="ESP32-C3 外设、寄存器与系统结构手册。",
        kind="pdf",
        filename="esp32-c3_technical_reference_manual_en.pdf",
    ),
    SourceRecord(
        category="硬件设计",
        title="ESP32-C3 Hardware Design Guidelines",
        url="https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/esp-hardware-design-guidelines-en-master-esp32c3.pdf",
        description="ESP32-C3 硬件原理图、PCB、启动与下载设计建议。",
        kind="pdf",
        filename="esp32-c3_hardware_design_guidelines_en.pdf",
    ),
]


MANIFEST_TITLE = "乐鑫 ESP 官方开发资料导入总览"
MANIFEST_FILENAME = "espressif_esp_official_docs_catalog.md"


def sanitize_filename(filename: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
    return safe or "imported.md"


def download_file(url: str) -> tuple[bytes, str | None]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get("Content-Type")


def build_manifest_text() -> str:
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [
        "# 乐鑫 ESP 官方开发资料导入总览",
        "",
        f"- 生成时间：{generated_at}",
        "- 来源策略：仅纳入 Espressif 官方站点 `docs.espressif.com` 与 `espressif.com`。",
        "- 文档选择原则：优先保留 `stable` 版 ESP-IDF 指南，并补充核心芯片 PDF 手册。",
        "- 当前覆盖重点：ESP32、ESP32-S3、ESP32-C3 三个常用系列。",
        "",
        "## 检索建议",
        "",
        "- 查开发流程：优先检索 ESP-IDF 编程指南、快速入门、`idf.py`、构建系统。",
        "- 查量产与升级：优先检索分区表、NVS、OTA、安全概述、Flash 加密。",
        "- 查硬件参数：优先检索 Datasheet、Hardware Design Guidelines。",
        "- 查寄存器与底层细节：优先检索 Technical Reference Manual。",
        "- 查烧录与镜像：优先检索 `esptool` 文档。",
        "",
    ]

    grouped: dict[str, list[SourceRecord]] = {}
    for source in WEB_SOURCES + PDF_SOURCES:
        grouped.setdefault(source.category, []).append(source)

    for category, items in grouped.items():
        lines.append(f"## {category}")
        lines.append("")
        for item in items:
            lines.append(f"### {item.title}")
            lines.append("")
            lines.append(f"- 类型：{'PDF' if item.kind == 'pdf' else '网页'}")
            lines.append(f"- 作用：{item.description}")
            lines.append(f"- 官方链接：{item.url}")
            lines.append("")

    lines.extend(
        [
            "## 使用边界",
            "",
            "- 本批导入偏向通用 ESP 开发资料，不覆盖所有模组、开发板、认证与测试专项文件。",
            "- 如果后续需要特定模组，例如 `ESP32-WROOM-32E`、`ESP32-C3-MINI-1`，建议再按模组名增补官方 datasheet。",
            "- 如果后续重点转向 Wi-Fi、Mesh、Matter、ESP-ADF、ESP-SR、ESP-AT，可继续按同样方式扩充专项知识库。",
            "",
        ]
    )
    return "\n".join(lines)


def delete_existing_manifest(storage: JSONStorage) -> None:
    for document in storage.list_documents():
        if document.title == MANIFEST_TITLE or document.filename == MANIFEST_FILENAME:
            storage.delete_document(document.id)


def import_manifest(storage: JSONStorage, upload_dir: Path) -> None:
    delete_existing_manifest(storage)
    destination = upload_dir / MANIFEST_FILENAME
    destination.write_text(build_manifest_text(), encoding="utf-8")
    extracted = extract_document_from_path(destination)
    storage.add_document(
        filename=MANIFEST_FILENAME,
        source_path=str(destination),
        text=extracted.text,
        title=MANIFEST_TITLE,
        source_type="file",
        source_format=extracted.source_format,
        encoding=extracted.encoding,
        document_ir=extracted.document_ir,
    )


def import_web_source(storage: JSONStorage, upload_dir: Path, source: SourceRecord) -> str:
    if storage.find_document_by_source_url(source.url):
        return "skipped"

    _, extracted = extract_web_document(source.url)
    safe_name = sanitize_filename(f"{source.title}.md")
    stamped_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{safe_name}"
    destination = upload_dir / stamped_name
    destination.write_text(extracted.text, encoding="utf-8")
    storage.add_document(
        filename=safe_name,
        source_path=str(destination),
        text=extracted.text,
        title=source.title,
        source_type="url",
        source_url=source.url,
        source_format=extracted.source_format,
        encoding=extracted.encoding,
        document_ir=extracted.document_ir,
    )
    return "imported"


def import_pdf_source(storage: JSONStorage, upload_dir: Path, source: SourceRecord) -> str:
    if storage.find_document_by_source_url(source.url):
        return "skipped"

    filename = source.filename or sanitize_filename(f"{source.title}.pdf")
    stamped_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{filename}"
    destination = upload_dir / stamped_name
    payload, content_type = download_file(source.url)
    if not payload.startswith(b"%PDF"):
        raise ValueError(
            f"{source.title} 下载结果不是 PDF，content-type={content_type or 'unknown'}，url={source.url}"
        )

    destination.write_bytes(payload)
    try:
        extracted = extract_document_from_path(destination)
        storage.add_document(
            filename=filename,
            source_path=str(destination),
            text=extracted.text,
            title=source.title,
            source_type="url",
            source_url=source.url,
            source_format=extracted.source_format,
            encoding=extracted.encoding,
            document_ir=extracted.document_ir,
            page_count=extracted.page_count,
        )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return "imported"


def main() -> None:
    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    upload_dir = Path(settings.rag_upload_dir)

    stats = {
        "web_imported": 0,
        "web_skipped": 0,
        "pdf_imported": 0,
        "pdf_skipped": 0,
    }

    for source in WEB_SOURCES:
        result = import_web_source(storage, upload_dir, source)
        print(f"{result}: {source.title}")
        stats[f"web_{result}"] += 1

    for source in PDF_SOURCES:
        result = import_pdf_source(storage, upload_dir, source)
        print(f"{result}: {source.title}")
        stats[f"pdf_{result}"] += 1

    import_manifest(storage, upload_dir)
    print(f"imported: {MANIFEST_TITLE}")
    print(
        "done: "
        f"web_imported={stats['web_imported']}, "
        f"web_skipped={stats['web_skipped']}, "
        f"pdf_imported={stats['pdf_imported']}, "
        f"pdf_skipped={stats['pdf_skipped']}"
    )


if __name__ == "__main__":
    main()
