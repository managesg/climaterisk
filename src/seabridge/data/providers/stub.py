from typing import Any
from ..base_provider import DataProvider


class StubProvider(DataProvider):
    """Returns zero/missing data. Used when a real provider is unavailable.

    All FeatureScore entries derived from this provider carry DataType.MISSING.
    """

    name: str = "stub"

    def __init__(self, stub_name: str = "stub", note: str = "No live data source configured."):
        self.name = stub_name
        self._note = note

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "available": False,
            "value": None,
            "note": self._note,
        }
