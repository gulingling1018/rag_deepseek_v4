#!/usr/bin/env python3
from datetime import UTC, datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.importers import fetch_web_document
from app.storage import JSONStorage


OFFICIAL_BT_URLS = [
    "https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/api-guides/bt-architecture/overview.html",
    "https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/api-guides/ble/index.html",
    "https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32/api-guides/classic-bt/index.html",
    "https://docs.espressif.com/projects/esp-idf/zh_CN/v5.1/esp32/api-reference/bluetooth/index.html",
    "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/bluetooth/nimble/index.html",
]


def sanitize_filename(filename: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
    return safe or "imported.md"


def main():
    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)

    imported = 0
    skipped = 0
    for url in OFFICIAL_BT_URLS:
        if storage.find_document_by_source_url(url):
            print(f"skip existing: {url}")
            skipped += 1
            continue

        title, text = fetch_web_document(url)
        safe_name = sanitize_filename(f"{title}.md")
        stamped_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{safe_name}"
        destination = Path(settings.rag_upload_dir) / stamped_name
        destination.write_text(text, encoding="utf-8")
        document = storage.add_document(
            filename=safe_name,
            source_path=str(destination),
            text=text,
            title=title,
            source_type="url",
            source_url=url,
        )
        imported += 1
        print(f"imported: {document.title}")

    print(f"done: imported={imported}, skipped={skipped}")


if __name__ == "__main__":
    main()
