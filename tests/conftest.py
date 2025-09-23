import os
import sys
from pathlib import Path
from importlib import reload
from typing import Dict

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class FakeInventoryClient:
    def __init__(self) -> None:
        self.available: Dict[str, int] = {}
        self.adjust_calls: Dict[str, int] = {}
        self.fail_adjust_for: Dict[str, bool] = {}

    def seed(self, book_id: str, qty: int) -> None:
        self.available[book_id] = qty

    def get_inventory(self, book_id: str):
        qty = self.available.get(book_id, 0)
        return {"inventory": {"quantity_available": qty}}

    def adjust(self, book_id: str, change: int, notes: str = ""):
        if self.fail_adjust_for.get(book_id):
            raise RuntimeError("upstream failure")
        cur = self.available.get(book_id, 0)
        new_qty = cur + change
        if new_qty < 0:
            raise RuntimeError("negative inventory")
        self.available[book_id] = new_qty
        self.adjust_calls[book_id] = self.adjust_calls.get(book_id, 0) + 1
        return {"ok": True, "new_quantity": new_qty}


@pytest.fixture()
def fake_inventory(monkeypatch) -> FakeInventoryClient:
    fake = FakeInventoryClient()
    import app.services as services
    monkeypatch.setattr(services, "InventoryClient", lambda: fake)
    return fake


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    db_file = tmp_path / "test_checkout.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    import app.database as database
    import app.models as models
    reload(database)
    reload(models)
    database.create_all()

    from app.main import app
    test_client = TestClient(app)
    return test_client


