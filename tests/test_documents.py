from pathlib import Path

import pytest

from brain_gateway.documents import (
    MAX_DOCUMENT_BYTES,
    DocumentError,
    load_documents,
    parse_document,
)


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


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("Sem título explícito", "título H1"),
        ("# \n\nConteúdo", "título H1"),
        ("# Primeiro\n\n# Segundo\n\nConteúdo", "título H1"),
        ("# Somente título", "conteúdo documental ausente"),
        ("# Título\n\n## Somente subtítulo", "conteúdo documental ausente"),
    ],
)
def test_document_requires_one_title_and_substantive_content(
    tmp_path: Path, body: str, message: str
) -> None:
    path = tmp_path / "invalid.md"
    frontmatter = VALID.split("---", 2)[1]
    path.write_text(f"---{frontmatter}---\n\n{body}\n", encoding="utf-8")

    with pytest.raises(DocumentError, match=message):
        parse_document(path, tmp_path)


def test_unknown_or_type_specific_frontmatter_fields_are_rejected(tmp_path: Path) -> None:
    for field in ("stats: active", "author: niyam"):
        path = tmp_path / "invalid.md"
        path.write_text(VALID.replace("supersedes:", f"supersedes:\n{field}"), encoding="utf-8")

        with pytest.raises(DocumentError, match="campos de frontmatter desconhecidos"):
            parse_document(path, tmp_path)


@pytest.mark.parametrize("scope", ['" "', "duas palavras", "../../fora", "a" * 121])
def test_scope_must_be_a_safe_identifier(tmp_path: Path, scope: str) -> None:
    path = tmp_path / "invalid.md"
    path.write_text(
        VALID.replace("scope: unnath-corporation", f"scope: {scope}"),
        encoding="utf-8",
    )

    with pytest.raises(DocumentError, match="scope inválido"):
        parse_document(path, tmp_path)


def test_proposal_author_must_be_a_safe_actor_identity(tmp_path: Path) -> None:
    proposal = (
        VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001")
        .replace("type: decision", "type: proposal")
        .replace("status: active", "status: pending")
        .replace(
            "supersedes:\n",
            'supersedes:\nauthor: "niyam admin"\ntimestamp: 2026-10-03T12:00:00+00:00\n',
        )
    )
    path = tmp_path / "proposal.md"
    path.write_text(proposal, encoding="utf-8")

    with pytest.raises(DocumentError, match="author inválido"):
        parse_document(path, tmp_path)


def test_proposal_created_date_must_match_timestamp(tmp_path: Path) -> None:
    proposal = (
        VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001")
        .replace("type: decision", "type: proposal")
        .replace("status: active", "status: pending")
        .replace(
            "supersedes:\n",
            "supersedes:\nauthor: niyam\ntimestamp: 2026-10-04T00:00:00+00:00\n",
        )
    )
    path = tmp_path / "proposal.md"
    path.write_text(proposal, encoding="utf-8")

    with pytest.raises(DocumentError, match="coincidir com a data do timestamp"):
        parse_document(path, tmp_path)


def test_duplicate_id(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "one.md").write_text(VALID, encoding="utf-8")
    (decisions / "two.md").write_text(VALID, encoding="utf-8")
    with pytest.raises(DocumentError, match="ID duplicado"):
        load_documents(tmp_path)


def test_load_documents_rejects_missing_or_non_directory_root(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(DocumentError, match="raiz do Brain ausente ou inválida"):
        load_documents(missing)

    regular_file = tmp_path / "brain.txt"
    regular_file.write_text("não é um diretório", encoding="utf-8")
    with pytest.raises(DocumentError, match="raiz do Brain ausente ou inválida"):
        load_documents(regular_file)


def test_symbolic_document_is_rejected(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    target = decisions / "target.md"
    target.write_text(VALID, encoding="utf-8")
    (decisions / "alias.md").symlink_to(target)

    with pytest.raises(DocumentError, match="links simbólicos não são permitidos"):
        load_documents(tmp_path)


def test_document_outside_root_is_rejected_before_parsing(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("not even frontmatter", encoding="utf-8")

    with pytest.raises(DocumentError, match="documento fora da raiz"):
        parse_document(outside, brain)


def test_oversized_document_is_rejected_before_reading(tmp_path: Path) -> None:
    path = tmp_path / "oversized.md"
    path.write_bytes(b"x" * (MAX_DOCUMENT_BYTES + 1))

    with pytest.raises(DocumentError, match="excede o limite"):
        parse_document(path, tmp_path)


@pytest.mark.parametrize("character", ["\x00", "\x07", "\x0b", "\x1f", "\x7f"])
def test_control_characters_are_rejected(tmp_path: Path, character: str) -> None:
    path = tmp_path / "invalid.md"
    path.write_text(VALID + character, encoding="utf-8")

    with pytest.raises(DocumentError, match="caractere de controle"):
        parse_document(path, tmp_path)


def test_pending_is_exclusive_to_proposals(tmp_path: Path) -> None:
    path = tmp_path / "decision.md"
    path.write_text(VALID.replace("status: active", "status: pending"), encoding="utf-8")
    with pytest.raises(DocumentError, match="exclusivo de propostas"):
        parse_document(path, tmp_path)


def test_proposal_requires_governance_metadata(tmp_path: Path) -> None:
    proposal = VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001").replace(
        "type: decision", "type: proposal"
    )
    path = tmp_path / "proposal.md"
    path.write_text(proposal, encoding="utf-8")
    with pytest.raises(DocumentError, match="proposta sem campos"):
        parse_document(path, tmp_path)


def test_proposal_cannot_be_active(tmp_path: Path) -> None:
    proposal = (
        VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001")
        .replace("type: decision", "type: proposal")
        .replace(
            "supersedes:\n",
            "supersedes:\nauthor: niyam\ntimestamp: 2026-10-03T12:00:00+00:00\n",
        )
    )
    path = tmp_path / "proposal.md"
    path.write_text(proposal, encoding="utf-8")
    with pytest.raises(DocumentError, match="deve permanecer pending"):
        parse_document(path, tmp_path)


def test_document_type_must_match_canonical_directory(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "decision.md").write_text(VALID, encoding="utf-8")

    with pytest.raises(DocumentError, match="type decision deve estar em decisions/"):
        load_documents(tmp_path)


def test_workflow_directories_accept_non_proposal_documents(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "decision.md").write_text(
        VALID.replace("status: active", "status: archived"), encoding="utf-8"
    )

    assert load_documents(tmp_path)[0].path == Path("archive/decision.md")


def test_proposal_must_remain_in_proposals_directory(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    proposal = (
        VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001")
        .replace("type: decision", "type: proposal")
        .replace("status: active", "status: pending")
        .replace(
            "supersedes:\n",
            "supersedes:\nauthor: niyam\ntimestamp: 2026-10-03T12:00:00+00:00\n",
        )
    )
    (inbox / "proposal.md").write_text(proposal, encoding="utf-8")

    with pytest.raises(DocumentError, match="type proposal deve estar em proposals/"):
        load_documents(tmp_path)


def test_supersedes_must_be_a_valid_existing_id(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "invalid.md").write_text(
        VALID.replace("supersedes:", "supersedes: ../escape"), encoding="utf-8"
    )
    with pytest.raises(DocumentError, match="supersedes inválido"):
        load_documents(tmp_path)

    (decisions / "invalid.md").write_text(
        VALID.replace("supersedes:", "supersedes: DEC-MISSING-001"), encoding="utf-8"
    )
    with pytest.raises(DocumentError, match="ID inexistente"):
        load_documents(tmp_path)


def test_document_cannot_supersede_itself(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "self.md").write_text(
        VALID.replace("supersedes:", "supersedes: DEC-TEST-001"), encoding="utf-8"
    )

    with pytest.raises(DocumentError, match="não pode superseder a si mesmo"):
        load_documents(tmp_path)


def test_supersedes_must_reference_same_document_type(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    knowledge = tmp_path / "knowledge"
    decisions.mkdir()
    knowledge.mkdir()
    predecessor = (
        VALID.replace("id: DEC-TEST-001", "id: KNOW-TEST-001")
        .replace("type: decision", "type: knowledge")
    )
    successor = VALID.replace("id: DEC-TEST-001", "id: DEC-TEST-002").replace(
        "supersedes:", "supersedes: KNOW-TEST-001"
    )
    (knowledge / "predecessor.md").write_text(predecessor, encoding="utf-8")
    (decisions / "successor.md").write_text(successor, encoding="utf-8")

    with pytest.raises(DocumentError, match="mesmo type"):
        load_documents(tmp_path)


def test_successor_cannot_predate_predecessor(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    predecessor = VALID.replace("created: 2026-10-03", "created: 2026-10-04")
    successor = VALID.replace("id: DEC-TEST-001", "id: DEC-TEST-002").replace(
        "supersedes:", "supersedes: DEC-TEST-001"
    )
    (decisions / "predecessor.md").write_text(predecessor, encoding="utf-8")
    (decisions / "successor.md").write_text(successor, encoding="utf-8")

    with pytest.raises(DocumentError, match="created não pode ser anterior"):
        load_documents(tmp_path)


def test_supersedes_graph_must_be_acyclic(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    first = VALID.replace("supersedes:", "supersedes: DEC-TEST-002")
    second = VALID.replace("DEC-TEST-001", "DEC-TEST-002").replace(
        "supersedes:", "supersedes: DEC-TEST-001"
    )
    (decisions / "first.md").write_text(first, encoding="utf-8")
    (decisions / "second.md").write_text(second, encoding="utf-8")

    with pytest.raises(DocumentError, match="ciclo em supersedes"):
        load_documents(tmp_path)


def test_supersedes_accepts_existing_acyclic_chain(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "first.md").write_text(VALID, encoding="utf-8")
    second = VALID.replace("DEC-TEST-001", "DEC-TEST-002").replace(
        "supersedes:", "supersedes: DEC-TEST-001"
    )
    (decisions / "second.md").write_text(second, encoding="utf-8")

    assert [document.id for document in load_documents(tmp_path)] == [
        "DEC-TEST-001",
        "DEC-TEST-002",
    ]


def proposal_targeting(target_id: str) -> str:
    return (
        VALID.replace("id: DEC-TEST-001", "id: PROP-TEST-001")
        .replace("type: decision", "type: proposal")
        .replace("status: active", "status: pending")
        .replace(
            "supersedes:\n",
            "supersedes:\nauthor: niyam\ntimestamp: 2026-10-03T12:00:00+00:00\n"
            f"target_id: {target_id}\n",
        )
    )


def test_proposal_target_must_exist_in_canonical_documents(tmp_path: Path) -> None:
    proposals = tmp_path / "proposals"
    proposals.mkdir()
    (proposals / "proposal.md").write_text(
        proposal_targeting("DEC-MISSING-001"), encoding="utf-8"
    )

    with pytest.raises(DocumentError, match="target_id referencia ID inexistente"):
        load_documents(tmp_path)


def test_proposal_cannot_target_itself(tmp_path: Path) -> None:
    proposals = tmp_path / "proposals"
    proposals.mkdir()
    (proposals / "proposal.md").write_text(
        proposal_targeting("PROP-TEST-001"), encoding="utf-8"
    )

    with pytest.raises(DocumentError, match="não pode apontar para si mesma"):
        load_documents(tmp_path)


def test_proposal_accepts_existing_target(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions"
    proposals = tmp_path / "proposals"
    decisions.mkdir()
    proposals.mkdir()
    (decisions / "decision.md").write_text(VALID, encoding="utf-8")
    (proposals / "proposal.md").write_text(
        proposal_targeting("DEC-TEST-001"), encoding="utf-8"
    )

    loaded = {document.id: document for document in load_documents(tmp_path)}
    assert loaded["PROP-TEST-001"].target_id == "DEC-TEST-001"
