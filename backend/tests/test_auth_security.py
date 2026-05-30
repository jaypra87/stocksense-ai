from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    assert h != "correct horse battery staple"
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)


def test_jwt_roundtrip() -> None:
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_jwt_rejects_tampered_token() -> None:
    token = create_access_token("user-123")
    assert decode_access_token(token + "x") is None
    assert decode_access_token("not.a.jwt") is None
