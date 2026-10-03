from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from .auth import authenticate
from .config import Settings
from .index import get_document, rebuild_index, search_documents
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


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        rebuild_index(resolved.brain_root, resolved.db_path)
        yield

    app = FastAPI(title="Unnath Brain Gateway", version="1.0.0", lifespan=lifespan)

    def actor_from_token(authorization: Annotated[str | None, Header()] = None) -> str:
        return authenticate(authorization, resolved.api_tokens)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/search")
    def search(
        q: Annotated[str, Query(min_length=1, max_length=500)],
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
        actor: str = Depends(actor_from_token),
    ) -> dict[str, object]:
        return {"actor": actor, "results": search_documents(resolved.db_path, q, limit)}

    @app.get("/api/v1/documents/{document_id}")
    def document(document_id: str, _: str = Depends(actor_from_token)) -> dict[str, object]:
        result = get_document(resolved.db_path, document_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="documento não encontrado")
        return result

    @app.post("/api/v1/context")
    def context_pack(request: ContextRequest, actor: str = Depends(actor_from_token)) -> dict[str, object]:
        combined_query = " ".join(
            value for value in (request.project, request.mission, request.query) if value
        )
        results = search_documents(resolved.db_path, combined_query, request.limit)
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
            **groups,
            "sources": sources,
        }

    @app.post("/api/v1/proposals", status_code=status.HTTP_201_CREATED)
    def proposal(request: ProposalRequest, actor: str = Depends(actor_from_token)) -> dict[str, object]:
        proposal_id, path, timestamp = create_proposal(
            resolved.brain_root,
            actor,
            request.title,
            request.content,
            request.target_id,
        )
        rebuild_index(resolved.brain_root, resolved.db_path)
        return {
            "id": proposal_id,
            "status": "pending",
            "author": actor,
            "timestamp": timestamp,
            "path": path.as_posix(),
        }

    return app
