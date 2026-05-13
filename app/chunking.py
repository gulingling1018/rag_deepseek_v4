import re


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；.!?;])\s*", text)
    return [part.strip() for part in parts if part.strip()]


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        units = [paragraph]
        if len(paragraph) > chunk_size:
            units = split_into_sentences(paragraph)

        for unit in units:
            if not current:
                current = unit
                continue

            candidate = f"{current}\n\n{unit}"
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            chunks.append(current)
            carry = current[-overlap:] if overlap > 0 else ""
            current = f"{carry}\n{unit}".strip()

    if current:
        chunks.append(current)

    return [chunk.strip() for chunk in chunks if chunk.strip()]
