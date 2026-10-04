from pathlib import Path
import sys

import pytest

from brain_gateway.cli import main


VALID = """---
id: KNOW-CLI-001
type: knowledge
status: active
scope: test
created: 2026-10-03
supersedes:
---
# Documento CLI
Conteúdo válido.
"""


def test_validate_command_does_not_require_api_tokens(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "document.md").write_text(VALID, encoding="utf-8")
    monkeypatch.setenv("BRAIN_ROOT", str(brain))
    monkeypatch.delenv("BRAIN_API_TOKENS", raising=False)
    monkeypatch.setattr(sys, "argv", ["brain", "validate"])

    main()

    assert capsys.readouterr().out == "Brain válido: 1 documento(s).\n"


def test_validate_command_reports_invalid_document(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    (brain / "invalid.md").write_text("# Sem frontmatter", encoding="utf-8")
    monkeypatch.setenv("BRAIN_ROOT", str(brain))
    monkeypatch.setattr(sys, "argv", ["brain", "validate"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    assert "Erro de validação" in capsys.readouterr().err


def test_rebuild_rejects_database_inside_canonical_root(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    brain = tmp_path / "brain"
    (brain / "knowledge").mkdir(parents=True)
    (brain / "knowledge" / "document.md").write_text(VALID, encoding="utf-8")
    database = brain / "data" / "brain.db"
    monkeypatch.setenv("BRAIN_ROOT", str(brain))
    monkeypatch.setenv("BRAIN_DB_PATH", str(database))
    monkeypatch.setattr(sys, "argv", ["brain", "rebuild"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 1
    assert "fora da fonte canônica" in capsys.readouterr().err
    assert not database.exists()
