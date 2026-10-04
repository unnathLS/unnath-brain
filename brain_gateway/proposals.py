from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
from uuid import uuid4


def _frontmatter_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def _safe_title(value: str) -> str:
    return re.sub(r"[\r\n]+", " ", value).strip()


def create_proposal(
    brain_root: Path,
    author: str,
    title: str,
    content: str,
    target_id: str | None = None,
) -> tuple[str, Path, str]:
    now = datetime.now(timezone.utc)
    proposal_id = f"PROP-{now:%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"
    relative_path = Path("proposals") / f"{proposal_id.lower()}.md"
    path = brain_root / relative_path
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    if brain_root.is_symlink() or path.parent.is_symlink():
        raise OSError("diretório de propostas não pode ser link simbólico")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.resolve().relative_to(brain_root.resolve())
    except ValueError as exc:
        raise OSError("diretório de propostas fora da raiz do Brain") from exc
    metadata = [
        "---",
        f"id: {proposal_id}",
        "type: proposal",
        "status: pending",
        "scope: unnath-corporation",
        f"created: {now.date().isoformat()}",
        "supersedes:",
        f"author: {_frontmatter_value(author)}",
        f"timestamp: {now.isoformat()}",
    ]
    if target_id:
        metadata.append(f"target_id: {_frontmatter_value(target_id)}")
    document = "\n".join(
        metadata
        + ["---", "", f"# {_safe_title(title)}", "", content.strip(), ""]
    )
    try:
        with temporary_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return proposal_id, relative_path, now.isoformat()
