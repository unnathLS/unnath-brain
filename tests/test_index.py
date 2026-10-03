from pathlib import Path

from brain_gateway.index import get_document, rebuild_index, search_documents


DOCUMENT = """---
id: KNOW-TEST-001
type: knowledge
status: active
scope: test
created: 2026-10-03
supersedes:
---
# Fonte canônica
O céu corporativo é azul.
"""


def test_index_search_get_and_rebuild(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    source = brain / "knowledge.md"
    source.write_text(DOCUMENT, encoding="utf-8")
    database = tmp_path / "index.db"

    assert rebuild_index(brain, database) == 1
    assert search_documents(database, "corporativo")[0]["id"] == "KNOW-TEST-001"
    assert get_document(database, "KNOW-TEST-001")["content_hash"]

    database.unlink()
    assert source.exists()
    assert rebuild_index(brain, database) == 1
    assert get_document(database, "KNOW-TEST-001")["path"] == "knowledge.md"


def test_files_outside_brain_are_not_indexed(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    (brain / "knowledge.md").write_text(DOCUMENT, encoding="utf-8")
    (tmp_path / ".env").write_text("BRAIN_API_TOKENS=top-secret", encoding="utf-8")

    database = tmp_path / "index.db"
    rebuild_index(brain, database)

    assert search_documents(database, "top-secret") == []

