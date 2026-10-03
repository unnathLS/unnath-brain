from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
    if document_type not in ALLOWED_TYPES:
        raise DocumentError(f"{path}: type inválido: {document_type}")
    if status not in ALLOWED_STATUSES:
        raise DocumentError(f"{path}: status inválido: {status}")
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
        supersedes=metadata.get("supersedes"),
        title=title,
        content=body,
        path=relative_path,
        content_hash=sha256(raw.encode("utf-8")).hexdigest(),
    )


def load_documents(root: Path) -> list[Document]:
    documents: list[Document] = []
    seen: dict[str, Path] = {}
    for path in sorted(root.rglob("*.md")):
        document = parse_document(path, root)
        if previous := seen.get(document.id):
            raise DocumentError(
                f"ID duplicado {document.id}: {previous.as_posix()} e {document.path.as_posix()}"
            )
        seen[document.id] = document.path
        documents.append(document)
    return documents

