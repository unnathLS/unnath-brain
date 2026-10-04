from hmac import compare_digest as real_compare_digest

import pytest
from fastapi import HTTPException

from brain_gateway import auth


def test_authentication_accepts_case_insensitive_scheme_and_scans_all_tokens(
    monkeypatch,
) -> None:
    compared: list[str] = []

    def observe(supplied: str, expected: str) -> bool:
        compared.append(expected)
        return real_compare_digest(supplied, expected)

    monkeypatch.setattr(auth, "compare_digest", observe)

    actor = auth.authenticate(
        "bearer token-a", {"unnatha": "token-a", "niyam": "token-b"}
    )

    assert actor == "unnatha"
    assert compared == ["token-a", "token-b"]


def test_authentication_rejects_ambiguous_headers() -> None:
    tokens = {"unnatha": "token-a"}

    for authorization in (
        None,
        "Basic token-a",
        "Bearer",
        "Bearer ",
        "Bearer  token-a",
        "Bearer token-a extra",
        "Bearer\ttoken-a",
    ):
        with pytest.raises(HTTPException) as raised:
            auth.authenticate(authorization, tokens)

        assert raised.value.status_code == 401
        assert raised.value.headers == {"WWW-Authenticate": "Bearer"}
