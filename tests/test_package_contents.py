"""What the published wheel and sdist contain.

Customers install the wheel: it must hold only the ``datalegion`` package, with no extra
top-level modules and no console commands (``lint``/``test`` once shipped onto every
customer's PATH). The sdist carries the source and tests, never repo tooling.
"""

import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    # Each straight from the source tree: a default build makes the wheel from the sdist, which
    # would hide a wheel misconfiguration behind the sdist's own include list.
    for target in ("--sdist", "--wheel"):
        subprocess.run(
            ["uv", "build", target, "--quiet", "--out-dir", str(out)], cwd=ROOT, check=True
        )
    return out


def test_wheel_ships_only_the_sdk_and_no_commands(dist: Path) -> None:
    (wheel,) = dist.glob("*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    top_level = {n.split("/")[0] for n in names if not n.split("/")[0].endswith(".dist-info")}
    assert top_level == {"datalegion"}
    assert not any(n.endswith("entry_points.txt") for n in names)


def test_wheel_marks_the_package_typed(dist: Path) -> None:
    # The package claims "Typing :: Typed"; without py.typed, type checkers ignore its hints.
    (wheel,) = dist.glob("*.whl")
    assert "datalegion/py.typed" in zipfile.ZipFile(wheel).namelist()


def test_sdist_carries_no_repo_tooling(dist: Path) -> None:
    (sdist,) = dist.glob("*.tar.gz")
    names = tarfile.open(sdist).getnames()
    leaked = [
        n
        for n in names
        if any(
            part in n.split("/")
            for part in (
                ".claude",
                ".github",
                "scripts",
                "lefthook.yml",
                "test_ci.py",
                "test_conventions.py",
                "_conventions.py",
            )
        )
    ]
    assert leaked == []
    assert any(n.endswith("src/datalegion/_client.py") for n in names)
