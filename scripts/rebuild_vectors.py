#!/usr/bin/env python3
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.storage import JSONStorage


def main() -> None:
    settings = get_settings()
    storage = JSONStorage(settings.rag_upload_dir, settings.rag_index_dir)
    chunks = storage.list_chunks()
    start_time = time.time()
    vectors = storage.build_vectors(chunks)
    spec = (vectors[0].provider, vectors[0].model, vectors[0].dimension) if vectors else ("n/a", "n/a", 0)
    print(
        f"rebuild_vectors_start chunks={len(chunks)} "
        f"provider={spec[0]} model={spec[1]} dim={spec[2]} collection={settings.rag_vector_collection}",
        flush=True,
    )
    storage.vector_store.write_records(vectors)
    consistency = storage.validate_vector_consistency(chunks)
    print(
        "rebuild_vectors_done "
        f"records={len(vectors)} seconds={time.time() - start_time:.1f} "
        f"missing={consistency['missing_vectors']} stale={consistency['stale_vectors']} orphan={consistency['orphan_vectors']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
