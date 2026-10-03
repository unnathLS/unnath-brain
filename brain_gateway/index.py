from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess

from .documents import load_documents


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    scope TEXT NOT NULL,
    created TEXT NOT NULL,
    supersedes TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    git_ref TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    id UNINDEXED,
    title,
    content,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def current_git_ref(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def rebuild_index(brain_root: Path, db_path: Path) -> int:
    documents = load_documents(brain_root)
    git_ref = current_git_ref(brain_root.parent)
    with connect(db_path) as connection:
        connection.execute("DELETE FROM documents_fts")
        connection.execute("DELETE FROM documents")
        for document in documents:
            connection.execute(
                """INSERT INTO documents
                (id, type, status, scope, created, supersedes, title, content, path, content_hash, git_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    document.id,
                    document.type,
                    document.status,
                    document.scope,
                    document.created,
                    document.supersedes,
                    document.title,
                    document.content,
                    document.path.as_posix(),
                    document.content_hash,
                    git_ref,
                ),
            )
            connection.execute(
                "INSERT INTO documents_fts (id, title, content) VALUES (?, ?, ?)",
                (document.id, document.title, document.content),
            )
    return len(documents)


def _row_to_dict(row: sqlite3.Row) -> dict[str, str | None]:
    return dict(row)


def get_document(db_path: Path, document_id: str) -> dict[str, str | None] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def _fts_query(query: str) -> str:
    terms = [part.replace('"', '""') for part in query.split() if part.strip()]
    if not terms:
        raise ValueError("consulta vazia")
    return " AND ".join(f'"{term}"*' for term in terms)


def search_documents(db_path: Path, query: str, limit: int = 10) -> list[dict[str, str | None]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT d.*, bm25(documents_fts, 0.0, 5.0, 1.0) AS score
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.id
            WHERE documents_fts MATCH ?
            ORDER BY score, d.id
            LIMIT ?""",
            (_fts_query(query), limit),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]
