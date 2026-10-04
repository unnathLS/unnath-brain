from __future__ import annotations

from contextlib import asynccontextmanager
import sqlite3
from threading import Lock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from .auth import authenticate
from .config import Settings
from .documents import ID_PATTERN
from .index import get_document, index_health, rebuild_index, search_documents
from .proposals import create_proposal


class ContextRequest(BaseModel):
    project: str | None = Field(default=None, max_length=120)
    mission: str | None = Field(default=None, max_length=500)
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class ProposalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)
    target_id: str | None = Field(default=None, max_length=80)

    @field_validator("title", "content")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("valor não pode conter apenas espaços")
        return value.strip()

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, value: str | None) -> str | None:
        if value is not None and not ID_PATTERN.fullmatch(value):
            raise ValueError("target_id inválido")
        return value


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_env()
    mutation_lock = Lock()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        with mutation_lock:
            rebuild_index(resolved.brain_root, resolved.db_path)
        yield

    app = FastAPI(title="Unnath Brain Gateway", version="1.0.0", lifespan=lifespan)

    def actor_from_token(authorization: Annotated[str | None, Header()] = None) -> str:
        return authenticate(authorization, resolved.api_tokens)

    @app.get("/health")
    def health() -> dict[str, object]:
        try:
            documents = index_health(resolved.db_path)
        except (FileNotFoundError, sqlite3.Error) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="índice indisponível",
            ) from exc
        return {"status": "ok", "documents": documents}

    @app.get("/api/v1/search")
    def search(
        q: Annotated[str, Query(min_length=1, max_length=500)],
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
        actor: str = Depends(actor_from_token),
    ) -> dict[str, object]:
        try:
            results = search_documents(resolved.db_path, q, limit)
        except (FileNotFoundError, sqlite3.Error) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="índice indisponível",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        return {"actor": actor, "results": results}

    @app.get("/api/v1/documents/{document_id}")
    def document(document_id: str, _: str = Depends(actor_from_token)) -> dict[str, object]:
        try:
            result = get_document(resolved.db_path, document_id)
        except (FileNotFoundError, sqlite3.Error) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="índice indisponível",
            ) from exc
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="documento não encontrado")
        return result

    @app.post("/api/v1/context")
    def context_pack(request: ContextRequest, actor: str = Depends(actor_from_token)) -> dict[str, object]:
        try:
            results = search_documents(
                resolved.db_path, request.query, request.limit, status="active"
            )
        except (FileNotFoundError, sqlite3.Error) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="índice indisponível",
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        groups: dict[str, list[dict[str, object]]] = {
            "decisions": [],
            "procedures": [],
            "knowledge": [],
            "other": [],
        }
        names = {"decision": "decisions", "procedure": "procedures", "knowledge": "knowledge"}
        sources = []
        for result in results:
            groups[names.get(str(result["type"]), "other")].append(result)
            sources.append(
                {
                    "id": result["id"],
                    "path": result["path"],
                    "content_hash": result["content_hash"],
                    "git_ref": result["git_ref"],
                }
            )
        return {
            "agent": actor,
            "project": request.project,
            "mission": request.mission,
            "query": request.query,
            **groups,
            "sources": sources,
        }

    @app.post("/api/v1/proposals", status_code=status.HTTP_201_CREATED)
    def proposal(request: ProposalRequest, actor: str = Depends(actor_from_token)) -> dict[str, object]:
        with mutation_lock:
            if request.target_id:
                try:
                    target = get_document(resolved.db_path, request.target_id)
                except (FileNotFoundError, sqlite3.Error) as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="índice indisponível",
                    ) from exc
                if not target:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="documento alvo não encontrado",
                    )
            proposal_id, path, timestamp = create_proposal(
                resolved.brain_root,
                actor,
                request.title,
                request.content,
                request.target_id,
            )
            try:
                rebuild_index(resolved.brain_root, resolved.db_path)
            except Exception as exc:
                try:
                    (resolved.brain_root / path).unlink(missing_ok=True)
                except OSError as rollback_error:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="falha ao reverter proposta não indexada",
                    ) from rollback_error
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="proposta não publicada",
                ) from exc
        return {
            "id": proposal_id,
            "status": "pending",
            "author": actor,
            "timestamp": timestamp,
            "path": path.as_posix(),
        }

    return app
