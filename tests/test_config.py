import json

import pytest

from brain_gateway.config import MIN_API_TOKEN_LENGTH, Settings


def token(character: str) -> str:
    return character * MIN_API_TOKEN_LENGTH


def test_settings_accept_strong_unique_tokens(monkeypatch) -> None:
    monkeypatch.setenv(
        "BRAIN_API_TOKENS",
        json.dumps({"unnatha": token("a"), "niyam": token("b")}),
    )

    settings = Settings.from_env()

    assert settings.api_tokens == {"unnatha": token("a"), "niyam": token("b")}


@pytest.mark.parametrize(
    "tokens",
    [
        {},
        {"": "a" * MIN_API_TOKEN_LENGTH},
        {" unnatha": "a" * MIN_API_TOKEN_LENGTH},
        {"unnatha admin": "a" * MIN_API_TOKEN_LENGTH},
        {"unnatha\nadmin": "a" * MIN_API_TOKEN_LENGTH},
        {"unnatha/../../admin": "a" * MIN_API_TOKEN_LENGTH},
        {"a" * 65: "a" * MIN_API_TOKEN_LENGTH},
        {"unnatha": "short"},
        {"unnatha": " " + "a" * MIN_API_TOKEN_LENGTH},
        {
            "unnatha": "a" * MIN_API_TOKEN_LENGTH,
            "niyam": "a" * MIN_API_TOKEN_LENGTH,
        },
    ],
)
def test_settings_reject_weak_or_ambiguous_tokens(monkeypatch, tokens) -> None:
    monkeypatch.setenv("BRAIN_API_TOKENS", json.dumps(tokens))

    with pytest.raises(RuntimeError, match="pelo menos 32 caracteres"):
        Settings.from_env()


def test_settings_reject_missing_or_invalid_json(monkeypatch) -> None:
    monkeypatch.delenv("BRAIN_API_TOKENS", raising=False)
    with pytest.raises(RuntimeError, match="não configurado"):
        Settings.from_env()

    monkeypatch.setenv("BRAIN_API_TOKENS", "not-json")
    with pytest.raises(RuntimeError, match="objeto JSON"):
        Settings.from_env()
