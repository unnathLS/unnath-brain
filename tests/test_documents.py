from pathlib import Path

import pytest

from brain_gateway.documents import DocumentError, load_documents, parse_document


VALID = """---
id: DEC-TEST-001
type: decision
status: active
scope: unnath-corporation
created: 2026-10-03
supersedes:
---

# Publicações externas

Publicações externas exigem autorização do Presidente.
"""


def test_parse_document(tmp_path: Path) -> None:
    path = tmp_path / "decision.md"
    path.write_text(VALID, encoding="utf-8")

    document = parse_document(path, tmp_path)

    assert document.id == "DEC-TEST-001"
    assert document.title == "Publicações externas"
    assert document.type == "decision"
    assert document.path == Path("decision.md")
    assert len(document.content_hash) == 64


@pytest.mark.parametrize(
    "invalid",
    [
        "# Sem frontmatter",
        VALID.replace("status: active\n", ""),
        VALID.replace("type: decision", "type: unknown"),
        VALID.replace("created: 2026-10-03", "created: ontem"),
        VALID.replace("id: DEC-TEST-001", "id: ../escape"),
    ],
)
def test_invalid_document(tmp_path: Path, invalid: str) -> None:
    path = tmp_path / "invalid.md"
    path.write_text(invalid, encoding="utf-8")
    with pytest.raises(DocumentError):
        parse_document(path, tmp_path)


def test_duplicate_id(tmp_path: Path) -> None:
    (tmp_path / "one.md").write_text(VALID, encoding="utf-8")
    (tmp_path / "two.md").write_text(VALID, encoding="utf-8")
    with pytest.raises(DocumentError, match="ID duplicado"):
        load_documents(tmp_path)

