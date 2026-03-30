"""Single place for project root (directory that contains configs/ and src/)."""

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
