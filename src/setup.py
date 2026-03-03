'''
setup.py
configure orekit
call config.py to load config
all shared imports and such go here
'''
from pathlib import Path

import yaml
import orekit
from orekit.pyhelpers import setup_orekit_curdir


def setup_orekit():
    """Initialize Orekit JVM and load auxiliary data path from configs/SALE.yaml."""
    vm = orekit.initVM()

    repo_root = Path(__file__).resolve().parent.parent
    sale_yaml = repo_root / "configs" / "SALE.yaml"

    with open(sale_yaml, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    orekit_data_path_str = config["orekit_data_path"]
    orekit_data_path = (repo_root / orekit_data_path_str).resolve()

    setup_orekit_curdir(filename=str(orekit_data_path))