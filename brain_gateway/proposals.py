from __future__ import annotations

from datetime import datetime, timezone
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
    path.parent.mkdir(parents=True, exist_ok=True)
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
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(document)
    return proposal_id, relative_path, now.isoformat()

