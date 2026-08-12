def estimate_tokens(text: str) -> int:
    """Heurística grosseira (~4 caracteres por token, regra de bolso comum pra texto em
    inglês/português) — nem Ollama nem OpenAI devolvem contagem real de tokens pro
    `LLMClient` deste projeto, então isso é só uma aproximação usada pro painel
    administrativo (custo estimado), não pra cobrança real."""
    return max(1, len(text) // 4)
