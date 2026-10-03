from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def test_all_installed_project_dependencies_are_constrained() -> None:
    constraints = {
        canonicalize_name(Requirement(line).name)
        for line in Path("constraints.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    installed = {
        canonicalize_name(distribution.metadata["Name"])
        for distribution in metadata.distributions()
    }
    unmanaged = installed - constraints - {"pip", "unnath-brain"}

    assert unmanaged == set()
