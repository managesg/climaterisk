from abc import ABC, abstractmethod
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_DIR = Path("/tmp/seabridge_provider_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class DataProvider(ABC):
    name: str = "base"
    cache_ttl_seconds: int = 86400  # 24 h default

    @abstractmethod
    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        """Fetch data for the given location. Always returns a dict.

        Keys depend on the provider. Missing values are returned as None.
        Implementors must NEVER raise — return a degraded result instead.
        """

    def is_available(self) -> bool:
        return True

    # ------------------------------------------------------------------ cache

    def _cache_key(self, lat: float, lon: float, **params: Any) -> str:
        raw = f"{self.name}:{lat:.4f}:{lon:.4f}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _get_cached(self, key: str) -> dict | None:
        path = _CACHE_DIR / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() - data["_ts"] < self.cache_ttl_seconds:
                return data["payload"]
        except Exception:
            pass
        return None

    def _set_cached(self, key: str, payload: dict) -> None:
        try:
            path = _CACHE_DIR / f"{key}.json"
            path.write_text(json.dumps({"_ts": time.time(), "payload": payload}))
        except Exception as exc:
            logger.debug("Cache write failed: %s", exc)
