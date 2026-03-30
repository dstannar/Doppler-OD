"""Orekit JVM init and orekit-data path from the mission YAML."""

from pathlib import Path

import orekit
import yaml
from orekit.pyhelpers import setup_orekit_curdir

from src.paths import repo_root


def setup_orekit(mission_config: str = "SALE.yaml") -> None:
    orekit.initVM()

    root = repo_root()
    mission_yaml = root / "configs" / mission_config
    if not mission_yaml.exists():
        mission_yaml = root / "configs" / "SALE.yaml"

    with open(mission_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    rel = config.get("orekit_data_path", "orekit-data")
    orekit_data_path = (root / str(rel)).resolve()
    setup_orekit_curdir(filename=str(orekit_data_path))
