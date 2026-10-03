from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
import re


ALLOWED_TYPES = {
    "decision",
    "procedure",
    "knowledge",
    "project",
    "company",
    "agent",
    "proposal",
}
ALLOWED_STATUSES = {"draft", "active", "superseded", "archived", "pending"}
REQUIRED_FIELDS = {"id", "type", "status", "scope", "created"}
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,79}$")
TYPE_DIRECTORIES = {
    "decision": "decisions",
    "procedure": "procedures",
    "knowledge": "knowledge",
    "project": "projects",
    "company": "company",
    "agent": "agents",
    "proposal": "proposals",
}
WORKFLOW_DIRECTORIES = {"archive", "inbox"}


class DocumentError(ValueError):
    pass


@dataclass(frozen=True)
class Document:
    id: str
    type: str
    status: str
    scope: str
    created: str
    supersedes: str | None
    title: str
    content: str
    path: Path
    content_hash: str


def _parse_scalar(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_document(path: Path, root: Path) -> Document:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentError(f"{path}: arquivo não está em UTF-8") from exc

    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        raise DocumentError(f"{path}: frontmatter ausente")
    try:
        closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise DocumentError(f"{path}: frontmatter não foi fechado") from exc

    metadata: dict[str, str | None] = {}
    for number, line in enumerate(lines[1:closing], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise DocumentError(f"{path}:{number}: campo de frontmatter inválido")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in metadata:
            raise DocumentError(f"{path}:{number}: campo vazio ou duplicado")
        metadata[key] = _parse_scalar(value)

    missing = sorted(field for field in REQUIRED_FIELDS if not metadata.get(field))
    if missing:
        raise DocumentError(f"{path}: campos obrigatórios ausentes: {', '.join(missing)}")

    document_id = str(metadata["id"])
    document_type = str(metadata["type"])
    status = str(metadata["status"])
    created = str(metadata["created"])
    if not ID_PATTERN.fullmatch(document_id):
        raise DocumentError(f"{path}: id inválido")
    supersedes = metadata.get("supersedes")
    if supersedes and not ID_PATTERN.fullmatch(supersedes):
        raise DocumentError(f"{path}: supersedes inválido")
    if document_type not in ALLOWED_TYPES:
        raise DocumentError(f"{path}: type inválido: {document_type}")
    if status not in ALLOWED_STATUSES:
        raise DocumentError(f"{path}: status inválido: {status}")
    if document_type == "proposal":
        missing_proposal = sorted(
            field for field in ("author", "timestamp") if not metadata.get(field)
        )
        if missing_proposal:
            raise DocumentError(
                f"{path}: proposta sem campos obrigatórios: {', '.join(missing_proposal)}"
            )
        if status != "pending":
            raise DocumentError(f"{path}: proposta deve permanecer pending")
        try:
            timestamp = datetime.fromisoformat(str(metadata["timestamp"]))
        except ValueError as exc:
            raise DocumentError(f"{path}: timestamp inválido") from exc
        if timestamp.tzinfo is None:
            raise DocumentError(f"{path}: timestamp deve incluir fuso horário")
        if target_id := metadata.get("target_id"):
            if not ID_PATTERN.fullmatch(target_id):
                raise DocumentError(f"{path}: target_id inválido")
    elif status == "pending":
        raise DocumentError(f"{path}: status pending é exclusivo de propostas")
    try:
        date.fromisoformat(created)
    except ValueError as exc:
        raise DocumentError(f"{path}: created deve usar YYYY-MM-DD") from exc

    body = "\n".join(lines[closing + 1 :]).strip()
    title = next(
        (line[2:].strip() for line in lines[closing + 1 :] if line.startswith("# ")),
        document_id,
    )
    try:
        relative_path = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise DocumentError(f"{path}: documento fora da raiz do Brain") from exc

    return Document(
        id=document_id,
        type=document_type,
        status=status,
        scope=str(metadata["scope"]),
        created=created,
        supersedes=supersedes,
        title=title,
        content=body,
        path=relative_path,
        content_hash=sha256(raw.encode("utf-8")).hexdigest(),
    )


def load_documents(root: Path) -> list[Document]:
    if not root.is_dir():
        raise DocumentError(f"{root}: raiz do Brain ausente ou inválida")
    documents: list[Document] = []
    seen: dict[str, Path] = {}
    for path in sorted(root.rglob("*.md")):
        document = parse_document(path, root)
        top_level = document.path.parts[0]
        expected = TYPE_DIRECTORIES[document.type]
        if top_level != expected and not (
            top_level in WORKFLOW_DIRECTORIES and document.type != "proposal"
        ):
            raise DocumentError(
                f"{document.path.as_posix()}: type {document.type} deve estar em "
                f"{expected}/"
            )
        if previous := seen.get(document.id):
            raise DocumentError(
                f"ID duplicado {document.id}: {previous.as_posix()} e {document.path.as_posix()}"
            )
        seen[document.id] = document.path
        documents.append(document)

    by_id = {document.id: document for document in documents}
    for document in documents:
        if document.supersedes == document.id:
            raise DocumentError(f"{document.path.as_posix()}: documento não pode superseder a si mesmo")
        if document.supersedes and document.supersedes not in by_id:
            raise DocumentError(
                f"{document.path.as_posix()}: supersedes referencia ID inexistente: "
                f"{document.supersedes}"
            )

    for document in documents:
        visited: set[str] = set()
        current = document
        while current.supersedes:
            if current.id in visited:
                raise DocumentError(f"ciclo em supersedes envolvendo {current.id}")
            visited.add(current.id)
            current = by_id[current.supersedes]
    return documents
