from dataclasses import dataclass
from typing import Any

from .data import WyomingService
from .devices import SatelliteDevice


@dataclass
class DomainDataItem:
    """Domain data item."""

    entry_data: dict[str, Any]

    service: WyomingService | None = None
    device: SatelliteDevice | None = None
