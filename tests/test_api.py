from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
from threading import Lock
import time

from fastapi.testclient import TestClient

from brain_gateway import api as api_module
from brain_gateway.api import create_app
from brain_gateway.config import Settings
from brain_gateway.index import rebuild_index


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


def test_responses_disable_intermediate_storage(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        responses = (
            client.get("/health"),
            client.get("/api/v1/search", params={"q": "Presidente"}),
            client.get(
                "/api/v1/search",
                params={"q": "Presidente"},
                headers=auth("token-a"),
            ),
        )

    for response in responses:
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Pragma"] == "no-cache"


def test_search_rejects_more_than_twenty_terms(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    query = " ".join(f"termo{number}" for number in range(21))
    with client:
        response = client.get(
            "/api/v1/search", params={"q": query}, headers=auth("token-a")
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "consulta excede o limite de 20 termos"


def test_health_fails_when_index_is_missing(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        (tmp_path / "brain.db").unlink()
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "índice indisponível"


def test_health_detects_and_recovers_from_fts_inconsistency(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    database = tmp_path / "brain.db"
    with client:
        with sqlite3.connect(database) as connection:
            connection.execute("DELETE FROM documents_fts")

        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "índice indisponível"

        rebuild_index(tmp_path / "brain", database)
        assert client.get("/health").json() == {"status": "ok", "documents": 1}


def test_health_detects_fts_content_mismatch(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    database = tmp_path / "brain.db"
    with client:
        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE documents_fts SET title = ? WHERE id = ?",
                ("Título adulterado", "DEC-TEST-001"),
            )

        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "índice indisponível"


def test_read_endpoints_fail_when_index_is_missing(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        (tmp_path / "brain.db").unlink()
        responses = (
            client.get(
                "/api/v1/search", params={"q": "Presidente"}, headers=auth("token-a")
            ),
            client.get("/api/v1/documents/DEC-TEST-001", headers=auth("token-a")),
            client.post(
                "/api/v1/context",
                json={"query": "Presidente"},
                headers=auth("token-a"),
            ),
        )
        for response in responses:
            assert response.status_code == 503
            assert response.json()["detail"] == "índice indisponível"
        assert not (tmp_path / "brain.db").exists()


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
        indexed = client.get(
            f"/api/v1/documents/{payload['id']}", headers=auth("token-a")
        ).json()
        assert indexed["author"] == "niyam"
        assert indexed["timestamp"] == payload["timestamp"]
        assert indexed["target_id"] == "DEC-TEST-001"


def test_pending_proposal_is_searchable_but_excluded_from_context(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    phrase = "hiperpropulsor"
    with client:
        created = client.post(
            "/api/v1/proposals",
            json={"title": "Proposta pendente", "content": phrase},
            headers=auth("token-b"),
        )
        assert created.status_code == 201

        search = client.get(
            "/api/v1/search", params={"q": phrase}, headers=auth("token-a")
        )
        assert search.status_code == 200
        assert search.json()["results"][0]["status"] == "pending"

        context = client.post(
            "/api/v1/context",
            json={"query": phrase},
            headers=auth("token-a"),
        )
        assert context.status_code == 200
        assert context.json()["other"] == []
        assert context.json()["sources"] == []


def test_proposal_rejects_invalid_content_before_writing(tmp_path: Path) -> None:
    client, brain = make_client(tmp_path)
    with client:
        for payload in (
            {"title": "   ", "content": "texto"},
            {"title": "Título", "content": "   "},
            {"title": "Título", "content": "texto", "target_id": "../escape"},
            {"title": "Título", "content": "# Outro título\n\nTexto"},
            {"title": "Título", "content": "## Apenas seção"},
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


def test_proposal_rejects_inactive_target_before_writing(tmp_path: Path) -> None:
    client, brain = make_client(tmp_path)
    decision = brain / "decisions" / "decision.md"
    decision.write_text(
        decision.read_text(encoding="utf-8").replace("status: active", "status: draft"),
        encoding="utf-8",
    )
    with client:
        rebuild_index(brain, tmp_path / "brain.db")
        response = client.post(
            "/api/v1/proposals",
            json={
                "title": "Não revisar rascunho",
                "content": "O alvo ainda não está vigente.",
                "target_id": "DEC-TEST-001",
            },
            headers=auth("token-a"),
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "documento alvo deve estar ativo e não ser proposta"
        assert list((brain / "proposals").iterdir()) == []


def test_proposal_is_rolled_back_when_index_rebuild_fails(
    tmp_path: Path, monkeypatch
) -> None:
    client, brain = make_client(tmp_path)
    with client:
        def fail_rebuild(*_args, **_kwargs) -> int:
            raise OSError("falha simulada no índice")

        monkeypatch.setattr(api_module, "rebuild_index", fail_rebuild)
        response = client.post(
            "/api/v1/proposals",
            json={"title": "Não persistir", "content": "Rebuild falhou."},
            headers=auth("token-a"),
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "proposta não publicada"
        assert list((brain / "proposals").iterdir()) == []
        assert client.get("/health").json() == {"status": "ok", "documents": 1}


def test_concurrent_proposal_mutations_are_serialized(
    tmp_path: Path, monkeypatch
) -> None:
    client, brain = make_client(tmp_path)
    original_create = api_module.create_proposal
    state_lock = Lock()
    active = 0
    maximum_active = 0

    def observed_create(*args, **kwargs):
        nonlocal active, maximum_active
        with state_lock:
            active += 1
            maximum_active = max(maximum_active, active)
        try:
            time.sleep(0.05)
            return original_create(*args, **kwargs)
        finally:
            with state_lock:
                active -= 1

    with client:
        monkeypatch.setattr(api_module, "create_proposal", observed_create)

        def submit(number: int):
            return client.post(
                "/api/v1/proposals",
                json={"title": f"Concorrente {number}", "content": "Conteúdo."},
                headers=auth("token-a"),
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(submit, (1, 2)))

        assert [response.status_code for response in responses] == [201, 201]
        assert maximum_active == 1
        assert len(list((brain / "proposals").glob("*.md"))) == 2
        assert client.get("/health").json() == {"status": "ok", "documents": 3}
