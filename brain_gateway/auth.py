from __future__ import annotations

from hmac import compare_digest

from fastapi import Header, HTTPException, status


def authenticate(authorization: str | None, tokens: dict[str, str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credencial ausente ou inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    supplied = authorization[7:]
    for actor, expected in tokens.items():
        if compare_digest(supplied, expected):
            return actor
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credencial ausente ou inválida",
        headers={"WWW-Authenticate": "Bearer"},
    )

