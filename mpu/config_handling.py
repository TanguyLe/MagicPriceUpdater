from pathlib import Path
from typing import Dict, Any

import yaml

CONDITIONS = ("MT", "NM", "EX", "GD", "LP", "PL", "PO")

LANGUAGES = (
    "English", "French", "German", "Spanish", "Italian", "Simplified Chinese",
    "Japanese", "Portuguese", "Russian", "Korean", "Traditional Chinese"
)


def load_config_file(config_file_path: Path) -> Dict[str, Any]:
    with config_file_path.open('r') as cfg_file:
        return yaml.safe_load(cfg_file)
