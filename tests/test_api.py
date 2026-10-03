from pathlib import Path

from fastapi.testclient import TestClient

from brain_gateway.api import create_app
from brain_gateway.config import Settings


DECISION = """---
id: DEC-TEST-001
type: decision
status: active
scope: unnath-corporation
created: 2026-10-03
supersedes:
---
# Autorização para publicações externas
Publicações externas exigem autorização do Presidente.
"""


def make_client(tmp_path: Path) -> tuple[TestClient, Path]:
    brain = tmp_path / "brain"
    (brain / "decisions").mkdir(parents=True)
    (brain / "proposals").mkdir()
    (brain / "decisions" / "decision.md").write_text(DECISION, encoding="utf-8")
    app = create_app(
        Settings(
            brain_root=brain,
            db_path=tmp_path / "brain.db",
            api_tokens={"unnatha": "token-a", "niyam": "token-b"},
        )
    )
    return TestClient(app), brain


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_and_invalid_auth(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/health").json() == {"status": "ok", "documents": 1}
        assert client.get("/api/v1/search", params={"q": "Presidente"}).status_code == 401
        assert client.get("/api/v1/search", params={"q": "Presidente"}, headers=auth("wrong")).status_code == 401
        assert client.get("/api/v1/search", params={"q": '"***"'}, headers=auth("token-a")).status_code == 422


def test_health_fails_when_index_is_missing(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        (tmp_path / "brain.db").unlink()
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "índice indisponível"


def test_two_consumers_find_same_document(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        for token, actor in (("token-a", "unnatha"), ("token-b", "niyam")):
            response = client.get(
                "/api/v1/search", params={"q": "publicações"}, headers=auth(token)
            )
            assert response.status_code == 200
            assert response.json()["actor"] == actor
            assert response.json()["results"][0]["id"] == "DEC-TEST-001"


def test_document_and_context(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        document = client.get("/api/v1/documents/DEC-TEST-001", headers=auth("token-a"))
        assert document.status_code == 200
        assert document.json()["content_hash"]
        context = client.post(
            "/api/v1/context",
            json={
                "project": "unnath-hq",
                "mission": "registrar execução futura",
                "query": "autorização Presidente",
                "limit": 5,
            },
            headers=auth("token-a"),
        )
        assert context.status_code == 200
        assert context.json()["agent"] == "unnatha"
        assert context.json()["project"] == "unnath-hq"
        assert context.json()["decisions"][0]["id"] == "DEC-TEST-001"
        assert context.json()["sources"][0]["path"] == "decisions/decision.md"


def test_proposal_is_pending_and_preserves_decision(tmp_path: Path) -> None:
    client, brain = make_client(tmp_path)
    original_path = brain / "decisions" / "decision.md"
    original = original_path.read_text(encoding="utf-8")
    with client:
        response = client.post(
            "/api/v1/proposals",
            json={
                "title": "Ajustar regra de publicações",
                "content": "Proposta de texto, ainda sem aprovação.",
                "target_id": "DEC-TEST-001",
            },
            headers=auth("token-b"),
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "pending"
        assert payload["author"] == "niyam"
        assert payload["timestamp"]
        proposal = (brain / payload["path"]).read_text(encoding="utf-8")
        assert "status: pending" in proposal
        assert 'author: "niyam"' in proposal
        assert "Proposta de texto" in proposal
        assert original_path.read_text(encoding="utf-8") == original


def test_proposal_rejects_invalid_content_before_writing(tmp_path: Path) -> None:
    client, brain = make_client(tmp_path)
    with client:
        for payload in (
            {"title": "   ", "content": "texto"},
            {"title": "Título", "content": "   "},
            {"title": "Título", "content": "texto", "target_id": "../escape"},
        ):
            response = client.post(
                "/api/v1/proposals", json=payload, headers=auth("token-a")
            )
            assert response.status_code == 422
        assert list((brain / "proposals").iterdir()) == []


def test_proposal_rejects_unknown_target_before_writing(tmp_path: Path) -> None:
    client, brain = make_client(tmp_path)
    with client:
        response = client.post(
            "/api/v1/proposals",
            json={
                "title": "Revisar documento ausente",
                "content": "Aguardar a criação do alvo.",
                "target_id": "DEC-UNKNOWN-001",
            },
            headers=auth("token-a"),
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "documento alvo não encontrado"
        assert list((brain / "proposals").iterdir()) == []
