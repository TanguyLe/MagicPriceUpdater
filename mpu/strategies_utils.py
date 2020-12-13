import json
import sys
from pathlib import Path
from typing import NamedTuple, Dict, Any, Optional

sys.path.append(str(Path(__file__).parent / "MPUStrategies"))


class StrategiesOptions(NamedTuple):
    current_price: Dict[str, Any]
    price_update: Dict[str, Any]


def get_strategies_options(strategies_options_path: Optional[Path]) -> StrategiesOptions:
    """Returns the current strategy options"""

    if strategies_options_path is not None:
        with strategies_options_path.open('r') as strategies_options_file:
            strategies_options = json.load(fp=strategies_options_file)

            return StrategiesOptions(
                current_price=strategies_options["current_price"],
                price_update=strategies_options["price_update"]
            )
    return StrategiesOptions(current_price={}, price_update={})
