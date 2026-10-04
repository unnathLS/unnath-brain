from pathlib import Path
import sqlite3
import subprocess

import pytest

from brain_gateway import index
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
    (brain / "knowledge").mkdir(parents=True)
    source = brain / "knowledge" / "knowledge.md"
    source.write_text(DOCUMENT, encoding="utf-8")
    database = tmp_path / "index.db"

    assert rebuild_index(brain, database) == 1
    assert search_documents(database, "corporativo")[0]["id"] == "KNOW-TEST-001"
    assert get_document(database, "KNOW-TEST-001")["content_hash"]

    database.unlink()
    assert source.exists()
    assert rebuild_index(brain, database) == 1
    assert get_document(database, "KNOW-TEST-001")["path"] == "knowledge/knowledge.md"


def test_files_outside_brain_are_not_indexed(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "knowledge.md").write_text(DOCUMENT, encoding="utf-8")
    (tmp_path / ".env").write_text("BRAIN_API_TOKENS=top-secret", encoding="utf-8")

    database = tmp_path / "index.db"
    rebuild_index(brain, database)

    assert search_documents(database, "top-secret") == []


def test_rebuild_migrates_governance_columns_in_existing_database(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "knowledge.md").write_text(DOCUMENT, encoding="utf-8")
    database = tmp_path / "index.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TABLE documents (
                id TEXT PRIMARY KEY, type TEXT NOT NULL, status TEXT NOT NULL,
                scope TEXT NOT NULL, created TEXT NOT NULL, supersedes TEXT,
                title TEXT NOT NULL, content TEXT NOT NULL, path TEXT NOT NULL,
                content_hash TEXT NOT NULL, git_ref TEXT
            )"""
        )

    rebuild_index(brain, database)

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(documents)")}
    assert {"author", "timestamp", "target_id"} <= columns


def test_connections_use_bounded_busy_timeout(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "knowledge.md").write_text(DOCUMENT, encoding="utf-8")
    database = tmp_path / "index.db"
    rebuild_index(brain, database)

    with index.connect_existing(database) as connection:
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert busy_timeout == index.SQLITE_BUSY_TIMEOUT_MS


def test_search_sanitizes_fts_syntax(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "knowledge.md").write_text(DOCUMENT, encoding="utf-8")
    database = tmp_path / "index.db"
    rebuild_index(brain, database)

    assert search_documents(database, '"corporativo"')[0]["id"] == "KNOW-TEST-001"
    assert search_documents(database, "corporativo OR *") == []
    with pytest.raises(ValueError, match="consulta vazia"):
        search_documents(database, '"***"')


def test_search_rejects_excessive_query_terms(tmp_path: Path) -> None:
    query = " ".join(f"termo{number}" for number in range(index.MAX_QUERY_TERMS + 1))

    with pytest.raises(ValueError, match="limite de 20 termos"):
        search_documents(tmp_path / "missing.db", query)


def test_git_ref_requires_tracked_unchanged_document(tmp_path: Path, monkeypatch) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    path = brain / "knowledge.md"
    path.write_text(DOCUMENT, encoding="utf-8")

    monkeypatch.setattr(
        index.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 0),
    )
    context = (tmp_path, "deadbeef")
    assert index._document_git_ref(context, brain, Path("knowledge.md")) == "deadbeef"

    def dirty_run(args, **kwargs):
        if "diff" in args:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(index.subprocess, "run", dirty_run)
    assert index._document_git_ref(context, brain, Path("knowledge.md")) is None
