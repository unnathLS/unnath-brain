from __future__ import annotations

from hmac import compare_digest

from fastapi import Header, HTTPException, status


def authenticate(authorization: str | None, tokens: dict[str, str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credencial ausente ou inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, separator, supplied = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not supplied
        or any(character.isspace() for character in supplied)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credencial ausente ou inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    matched_actor = None
    for actor, expected in tokens.items():
        if compare_digest(supplied, expected):
            matched_actor = actor
    if matched_actor:
        return matched_actor
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credencial ausente ou inválida",
        headers={"WWW-Authenticate": "Bearer"},
    )
