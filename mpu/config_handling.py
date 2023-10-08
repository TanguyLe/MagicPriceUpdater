from pathlib import Path
from typing import Any, Dict

import yaml


def load_config_file(config_file_path: Path) -> Dict[str, Any]:
    with config_file_path.open("r") as cfg_file:
        return yaml.safe_load(cfg_file)
