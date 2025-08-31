"""
HTTP client for Inventory service.
"""

import time
from typing import Any, Dict
import httpx

from .config import load_config


class InventoryError(Exception):
    pass


class InventoryClient:
    def __init__(self) -> None:
        cfg = load_config()
        self.base = cfg.inventory_base_url.rstrip("/")
        self.timeout = httpx.Timeout(cfg.request_timeout_seconds)
        self.retry_attempts = cfg.retry_attempts

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_exc = None
        for attempt in range(self.retry_attempts + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.request(method, url, **kwargs)
                    if resp.status_code >= 500:
                        raise InventoryError(f"Upstream 5xx: {resp.status_code}")
                    return resp
            except Exception as exc:  # retry on network/5xx
                last_exc = exc
                if attempt < self.retry_attempts:
                    time.sleep(0.2 * (2 ** attempt))
                else:
                    raise InventoryError(str(last_exc))
        raise InventoryError("Unexpected client flow")

    def get_inventory(self, book_id: str) -> Dict[str, Any]:
        url = f"{self.base}/api/v1/inventory/{book_id}"
        resp = self._request("GET", url)
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        return resp.json()

    def adjust(self, book_id: str, change: int, notes: str = "") -> Dict[str, Any]:
        url = f"{self.base}/api/v1/inventory/adjust?book_id={book_id}"
        payload = {"quantity_change": change, "notes": notes}
        resp = self._request("POST", url, json=payload)
        resp.raise_for_status()
        return resp.json()


