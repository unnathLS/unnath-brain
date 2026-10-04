from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
import re

from .config import ACTOR_PATTERN


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
COMMON_FIELDS = REQUIRED_FIELDS | {"supersedes"}
PROPOSAL_FIELDS = {"author", "timestamp", "target_id"}
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,79}$")
SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
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
    target_id: str | None
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
        relative_path = path.absolute().relative_to(root.absolute())
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise DocumentError(f"{path}: documento fora da raiz do Brain") from exc

    candidate = root.absolute()
    if candidate.is_symlink():
        raise DocumentError(f"{path}: links simbólicos não são permitidos no Brain")
    for part in relative_path.parts:
        candidate /= part
        if candidate.is_symlink():
            raise DocumentError(f"{path}: links simbólicos não são permitidos no Brain")

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
    scope = str(metadata["scope"])
    if not ID_PATTERN.fullmatch(document_id):
        raise DocumentError(f"{path}: id inválido")
    supersedes = metadata.get("supersedes")
    if supersedes and not ID_PATTERN.fullmatch(supersedes):
        raise DocumentError(f"{path}: supersedes inválido")
    if document_type not in ALLOWED_TYPES:
        raise DocumentError(f"{path}: type inválido: {document_type}")
    allowed_fields = COMMON_FIELDS | (PROPOSAL_FIELDS if document_type == "proposal" else set())
    unknown_fields = sorted(metadata.keys() - allowed_fields)
    if unknown_fields:
        raise DocumentError(
            f"{path}: campos de frontmatter desconhecidos: {', '.join(unknown_fields)}"
        )
    if status not in ALLOWED_STATUSES:
        raise DocumentError(f"{path}: status inválido: {status}")
    if not SCOPE_PATTERN.fullmatch(scope):
        raise DocumentError(f"{path}: scope inválido")
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
        if not ACTOR_PATTERN.fullmatch(str(metadata["author"])):
            raise DocumentError(f"{path}: author inválido")
        try:
            timestamp = datetime.fromisoformat(str(metadata["timestamp"]))
        except ValueError as exc:
            raise DocumentError(f"{path}: timestamp inválido") from exc
        if timestamp.tzinfo is None:
            raise DocumentError(f"{path}: timestamp deve incluir fuso horário")
        target_id = metadata.get("target_id")
        if target_id:
            if not ID_PATTERN.fullmatch(target_id):
                raise DocumentError(f"{path}: target_id inválido")
    elif status == "pending":
        raise DocumentError(f"{path}: status pending é exclusivo de propostas")
    else:
        target_id = None
    try:
        created_date = date.fromisoformat(created)
    except ValueError as exc:
        raise DocumentError(f"{path}: created deve usar YYYY-MM-DD") from exc
    if document_type == "proposal" and timestamp.date() != created_date:
        raise DocumentError(f"{path}: created deve coincidir com a data do timestamp")

    body_lines = lines[closing + 1 :]
    titles = [line[2:].strip() for line in body_lines if line.startswith("# ")]
    if len(titles) != 1 or not titles[0]:
        raise DocumentError(f"{path}: documento deve ter exatamente um título H1 não vazio")
    if not any(
        line.strip() and not line.lstrip().startswith("#") for line in body_lines
    ):
        raise DocumentError(f"{path}: conteúdo documental ausente")
    body = "\n".join(body_lines).strip()
    title = titles[0]
    return Document(
        id=document_id,
        type=document_type,
        status=status,
        scope=scope,
        created=created,
        supersedes=supersedes,
        target_id=target_id,
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
        if document.target_id == document.id:
            raise DocumentError(f"{document.path.as_posix()}: proposta não pode apontar para si mesma")
        if document.target_id and document.target_id not in by_id:
            raise DocumentError(
                f"{document.path.as_posix()}: target_id referencia ID inexistente: "
                f"{document.target_id}"
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
