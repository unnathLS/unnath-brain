from pathlib import Path

import pytest

from brain_gateway.documents import DocumentError
from brain_gateway.proposals import create_proposal


def test_proposal_is_published_atomically(tmp_path: Path, monkeypatch) -> None:
    original_replace = Path.replace
    observed: dict[str, object] = {}

    def inspect_replace(source: Path, target: Path) -> Path:
        observed["source"] = source
        observed["target"] = target
        observed["visible_markdown"] = list(tmp_path.rglob("*.md"))
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", inspect_replace)

    _, relative_path, _ = create_proposal(
        tmp_path, "unnatha", "Mudança atômica", "Conteúdo completo."
    )

    assert observed["source"] == tmp_path / relative_path.with_suffix(".md.tmp")
    assert observed["target"] == tmp_path / relative_path
    assert observed["visible_markdown"] == []
    assert (tmp_path / relative_path).is_file()
    assert list(tmp_path.rglob("*.tmp")) == []


def test_failed_atomic_publish_leaves_no_partial_file(
    tmp_path: Path, monkeypatch
) -> None:
    def fail_replace(source: Path, target: Path) -> Path:
        raise OSError("falha simulada ao publicar")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="falha simulada"):
        create_proposal(tmp_path, "unnatha", "Falha", "Não deve aparecer.")

    assert list(tmp_path.rglob("*.md")) == []
    assert list(tmp_path.rglob("*.tmp")) == []


def test_proposal_directory_cannot_be_a_symbolic_link(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    outside = tmp_path / "outside"
    brain.mkdir()
    outside.mkdir()
    (brain / "proposals").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError, match="link simbólico"):
        create_proposal(brain, "unnatha", "Não escapar", "Conteúdo protegido.")

    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("content", ["# Segundo título\n\nTexto.", "## Apenas seção"])
def test_invalid_canonical_proposal_is_not_published(
    tmp_path: Path, content: str
) -> None:
    with pytest.raises(DocumentError):
        create_proposal(tmp_path, "unnatha", "Título", content)

    assert list(tmp_path.rglob("*.md")) == []
    assert list(tmp_path.rglob("*.tmp")) == []
