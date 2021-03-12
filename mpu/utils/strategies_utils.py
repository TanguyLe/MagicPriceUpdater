import enum
import sys
from pathlib import Path
from typing import Any, Dict, NamedTuple

sys.path.append(str(Path(__file__).parent.parent / "MPUStrategies"))

from mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu_strategies.errors import SuitableExamplesShortage
from mpu_strategies.price_update import PriceUpdater


class StrategiesOptions(NamedTuple):
    current_price: Dict[str, Any]
    price_update: Dict[str, Any]


def get_strategies_options(config: dict) -> StrategiesOptions:
    """Returns the current strategy options"""

    strategies_options = config.get("strategies_options", None)
    if strategies_options is None or not strategies_options:
        return StrategiesOptions(current_price={}, price_update={})

    return StrategiesOptions(
        current_price=strategies_options["current_price"],
        price_update=strategies_options["price_update"],
    )


CurrentPriceStrat = enum.Enum(
    "CurrentPriceStrat",
    {strat: strat for strat in CurrentPriceComputer.get_available_strategies()},
)
PriceUpdaterStrat = enum.Enum(
    "PriceUpdaterStrat",
    {strat: strat for strat in PriceUpdater.get_available_strategies()},
)

__all__ = [
    "CurrentPriceStrat",
    "PriceUpdaterStrat",
    "PriceUpdater",
    "CurrentPriceComputer",
    "get_strategies_options",
    "SuitableExamplesShortage",
]
