from pathlib import Path
import re


def test_python_base_image_is_pinned_by_digest() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert re.search(
        r"^FROM python:3\.12-slim@sha256:[0-9a-f]{64} AS base$",
        dockerfile,
        flags=re.MULTILINE,
    )
