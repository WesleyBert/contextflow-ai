from uuid import uuid4

import pytest

from src.infrastructure.security.jwt import create_access_token, create_refresh_token, decode_token
from src.infrastructure.security.password import hash_password, verify_password


def test_hash_password_does_not_store_plaintext() -> None:
    hashed = hash_password("minha-senha-secreta")

    assert hashed != "minha-senha-secreta"


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("minha-senha-secreta")

    assert verify_password("minha-senha-secreta", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("minha-senha-secreta")

    assert verify_password("outra-senha", hashed) is False


def test_access_token_roundtrip() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_refresh_token_roundtrip() -> None:
    user_id = uuid4()

    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_decode_token_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        decode_token("isso-nao-e-um-jwt-valido")
