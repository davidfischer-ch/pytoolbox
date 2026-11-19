"""Tests for the packaging configuration of pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Final

from setuptools.config import expand

ROOT_DIRECTORY: Final[Path] = Path(__file__).resolve().parent.parent


def test_packages_discovered_are_pytoolbox_alone(tmp_path: Path) -> None:
    """The packages discovered are pytoolbox alone, whatever else the checkout holds."""
    project = tomllib.loads((ROOT_DIRECTORY / 'pyproject.toml').read_text(encoding='utf-8'))

    for directory in ('pytoolbox', 'build/lib/pytoolbox', 'docs/source'):
        (tmp_path / directory).mkdir(parents=True)
    (tmp_path / 'pytoolbox' / '__init__.py').touch()
    (tmp_path / 'build' / 'lib' / 'pytoolbox' / '__init__.py').touch()

    assert expand.find_packages(
        **project['tool']['setuptools']['packages']['find'],
        root_dir=tmp_path,
    ) == ['pytoolbox']
