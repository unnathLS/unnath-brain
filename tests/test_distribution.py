from pathlib import Path
import re


def test_python_base_image_is_pinned_by_digest() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert re.search(
        r"^FROM python:3\.12-slim@sha256:[0-9a-f]{64} AS base$",
        dockerfile,
        flags=re.MULTILINE,
    )


def test_runtime_does_not_log_request_paths_or_queries() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert '"--no-access-log"' in dockerfile


def test_compose_confines_runtime_container() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert re.search(r"^    read_only: true$", compose, flags=re.MULTILINE)
    assert re.search(r"^    cap_drop:\n      - ALL$", compose, flags=re.MULTILINE)
    assert "      - no-new-privileges:true" in compose
    assert "      - /tmp:rw,noexec,nosuid,size=64m" in compose


def test_compose_bounds_runtime_logs() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert re.search(r"^    logging:\n      driver: json-file$", compose, flags=re.MULTILINE)
    assert re.search(r'^        max-size: "10m"$', compose, flags=re.MULTILINE)
    assert re.search(r'^        max-file: "3"$', compose, flags=re.MULTILINE)


def test_compose_bounds_runtime_resources() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert re.search(r'^    cpus: "1\.0"$', compose, flags=re.MULTILINE)
    assert re.search(r"^    mem_limit: 512m$", compose, flags=re.MULTILINE)
    assert re.search(r"^    pids_limit: 128$", compose, flags=re.MULTILINE)
