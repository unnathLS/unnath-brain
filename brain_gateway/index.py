from __future__ import annotations

from pathlib import Path
import re
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
    author TEXT,
    timestamp TEXT,
    target_id TEXT,
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

GOVERNANCE_COLUMNS = {
    "author": "TEXT",
    "timestamp": "TEXT",
    "target_id": "TEXT",
}


def _ensure_governance_columns(connection: sqlite3.Connection) -> None:
    existing = {
        row[1] for row in connection.execute("PRAGMA table_info(documents)").fetchall()
    }
    for name, definition in GOVERNANCE_COLUMNS.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    _ensure_governance_columns(connection)
    return connection


def connect_existing(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _git_context(start: Path) -> tuple[Path, str] | None:
    try:
        root_result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
        root = Path(root_result.stdout.strip())
        head_result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    head = head_result.stdout.strip()
    return (root, head) if head else None


def _document_git_ref(
    context: tuple[Path, str] | None, brain_root: Path, document_path: Path
) -> str | None:
    if not context:
        return None
    repository_root, head = context
    absolute_path = brain_root / document_path
    try:
        relative_path = absolute_path.resolve().relative_to(repository_root.resolve()).as_posix()
        subprocess.run(
            ["git", "-C", str(repository_root), "ls-files", "--error-unmatch", "--", relative_path],
            capture_output=True,
            timeout=2,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repository_root), "diff", "--quiet", "HEAD", "--", relative_path],
            capture_output=True,
            timeout=2,
            check=True,
        )
    except (ValueError, FileNotFoundError, subprocess.SubprocessError):
        return None
    return head


def rebuild_index(brain_root: Path, db_path: Path) -> int:
    documents = load_documents(brain_root)
    git_context = _git_context(brain_root)
    with connect(db_path) as connection:
        connection.execute("DELETE FROM documents_fts")
        connection.execute("DELETE FROM documents")
        for document in documents:
            connection.execute(
                """INSERT INTO documents
                (id, type, status, scope, created, supersedes, author, timestamp,
                 target_id, title, content, path, content_hash, git_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    document.id,
                    document.type,
                    document.status,
                    document.scope,
                    document.created,
                    document.supersedes,
                    document.author,
                    document.timestamp,
                    document.target_id,
                    document.title,
                    document.content,
                    document.path.as_posix(),
                    document.content_hash,
                    _document_git_ref(git_context, brain_root, document.path),
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
    with connect_existing(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def index_health(db_path: Path) -> int:
    with connect_existing(db_path) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchall()
        if not quick_check or any(row[0] != "ok" for row in quick_check):
            raise sqlite3.DatabaseError("falha na integridade do SQLite")
        document_count = int(
            connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        )
        fts_count = int(
            connection.execute("SELECT COUNT(*) FROM documents_fts").fetchone()[0]
        )
        missing_fts = connection.execute(
            """SELECT 1
            FROM documents AS d
            LEFT JOIN documents_fts AS f ON f.id = d.id
            WHERE f.id IS NULL
            LIMIT 1"""
        ).fetchone()
        orphaned_fts = connection.execute(
            """SELECT 1
            FROM documents_fts AS f
            LEFT JOIN documents AS d ON d.id = f.id
            WHERE d.id IS NULL
            LIMIT 1"""
        ).fetchone()
        content_mismatch = connection.execute(
            """SELECT 1
            FROM documents AS d
            JOIN documents_fts AS f ON f.id = d.id
            WHERE f.title != d.title OR f.content != d.content
            LIMIT 1"""
        ).fetchone()
        if document_count != fts_count or missing_fts or orphaned_fts or content_mismatch:
            raise sqlite3.DatabaseError("índice textual inconsistente")
    return document_count


def _fts_query(query: str) -> str:
    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    if not terms:
        raise ValueError("consulta vazia")
    return " AND ".join(f'"{term}"*' for term in terms)


def search_documents(
    db_path: Path,
    query: str,
    limit: int = 10,
    status: str | None = None,
) -> list[dict[str, str | None]]:
    status_clause = " AND d.status = ?" if status else ""
    parameters: tuple[object, ...] = (
        (_fts_query(query), status, limit) if status else (_fts_query(query), limit)
    )
    with connect_existing(db_path) as connection:
        rows = connection.execute(
            f"""SELECT d.*, bm25(documents_fts, 0.0, 5.0, 1.0) AS score
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.id
            WHERE documents_fts MATCH ?{status_clause}
            ORDER BY score, d.id
            LIMIT ?""",
            parameters,
        ).fetchall()
    return [_row_to_dict(row) for row in rows]
