def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide o texto em pedaços de até `chunk_size` caracteres, com sobreposição
    de `overlap` caracteres entre pedaços consecutivos (pra não perder contexto que
    caiu bem na fronteira de dois chunks). Quebra em espaços, não no meio de uma palavra."""
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            break_point = text.rfind(" ", start, end)
            if break_point > start:
                end = break_point

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
