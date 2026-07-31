from src.infrastructure.text.chunker import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ", chunk_size=100, overlap=10) == []
    assert chunk_text("", chunk_size=100, overlap=10) == []


def test_text_shorter_than_chunk_size_returns_single_chunk() -> None:
    assert chunk_text("um texto curto", chunk_size=100, overlap=10) == ["um texto curto"]


def test_splits_long_text_into_multiple_chunks() -> None:
    text = " ".join(f"palavra{i}" for i in range(200))

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1
    assert all(len(chunk) <= 50 for chunk in chunks)


def test_breaks_at_word_boundary_not_mid_word() -> None:
    text = "a" * 40 + " " + "b" * 40

    chunks = chunk_text(text, chunk_size=45, overlap=0)

    assert chunks[0] == "a" * 40
    assert chunks[1] == "b" * 40


def test_consecutive_chunks_overlap() -> None:
    text = " ".join(f"palavra{i:03d}" for i in range(100))

    chunks = chunk_text(text, chunk_size=60, overlap=20)

    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert set(first_words) & set(second_words), "chunks consecutivos deveriam se sobrepor"


def test_first_and_last_words_are_preserved() -> None:
    words = [f"w{i}" for i in range(50)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=30, overlap=5)

    assert words[0] in chunks[0]
    assert words[-1] in chunks[-1]
