import os
import sys
import time
from decimal import Decimal

import httpx


INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:8001")
CHECKOUT_URL = os.getenv("CHECKOUT_URL", "http://localhost:8002")


def wait_healthy(url: str, path: str = "/health", timeout_s: int = 30) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = httpx.get(url + path, timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service at {url} not healthy in time")


def main() -> int:
    book_id = "smoke-book-1"
    unit_price = Decimal("9.99")

    print("Waiting for services to become healthy...")
    wait_healthy(INVENTORY_URL)
    wait_healthy(CHECKOUT_URL)

    print("Seeding inventory...")
    adj = {"quantity_change": 5, "notes": "smoke-seed"}
    r = httpx.post(f"{INVENTORY_URL}/api/v1/inventory/adjust", params={"book_id": book_id}, json=adj, timeout=5)
    r.raise_for_status()

    print("Placing order via checkout...")
    order = {
        "userId": "smoke-user",
        "items": [
            {"bookId": book_id, "qty": 2, "unitPrice": str(unit_price)}
        ]
    }
    headers = {"Idempotency-Key": "smoke-key-1"}
    r = httpx.post(f"{CHECKOUT_URL}/orders", json=order, headers=headers, timeout=5)
    r.raise_for_status()
    data = r.json()
    assert data["status"] == "CONFIRMED"
    print(f"Order created: {data['orderId']}")

    print("Verifying inventory decreased...")
    r = httpx.get(f"{INVENTORY_URL}/api/v1/inventory/{book_id}", timeout=5)
    r.raise_for_status()
    inv = r.json()
    qty = inv["inventory"]["quantity_available"]
    if qty != 3:
        raise AssertionError(f"Expected remaining 3, got {qty}")

    print("Smoke test PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Smoke test FAILED: {e}", file=sys.stderr)
        sys.exit(1)


