from decimal import Decimal


def test_create_order_happy_path(client, fake_inventory):
    fake_inventory.seed("book-1", 5)
    payload = {
        "userId": "user-1",
        "items": [
            {"bookId": "book-1", "qty": 2, "unitPrice": "10.00"}
        ]
    }
    resp = client.post("/orders", json=payload, headers={"Idempotency-Key": "abc"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "CONFIRMED"
    assert Decimal(str(data["total"])) == Decimal("20.00")
    assert fake_inventory.available["book-1"] == 3


def test_create_order_insufficient_stock(client, fake_inventory):
    fake_inventory.seed("book-1", 1)
    payload = {
        "userId": "user-1",
        "items": [
            {"bookId": "book-1", "qty": 2, "unitPrice": "10.00"}
        ]
    }
    resp = client.post("/orders", json=payload)
    assert resp.status_code == 409


def test_idempotency_replay_returns_same_order(client, fake_inventory):
    fake_inventory.seed("book-1", 5)
    payload = {
        "userId": "user-1",
        "items": [
            {"bookId": "book-1", "qty": 1, "unitPrice": "7.50"}
        ]
    }
    k = {"Idempotency-Key": "same-key"}
    r1 = client.post("/orders", json=payload, headers=k)
    r2 = client.post("/orders", json=payload, headers=k)
    assert r1.status_code == 201
    assert r2.status_code in (200, 201)
    d1 = r1.json(); d2 = r2.json()
    assert d1["orderId"] == d2["orderId"]


def test_compensation_on_adjust_failure(client, fake_inventory):
    fake_inventory.seed("book-2", 3)
    fake_inventory.fail_adjust_for["book-2"] = True
    payload = {
        "userId": "user-1",
        "items": [
            {"bookId": "book-2", "qty": 1, "unitPrice": "5.00"}
        ]
    }
    resp = client.post("/orders", json=payload)
    assert resp.status_code in (400, 502)
    assert fake_inventory.available["book-2"] == 3


def test_get_order(client, fake_inventory):
    fake_inventory.seed("book-3", 2)
    payload = {
        "userId": "user-9",
        "items": [
            {"bookId": "book-3", "qty": 2, "unitPrice": "3.00"}
        ]
    }
    r = client.post("/orders", json=payload)
    assert r.status_code == 201
    oid = r.json()["orderId"]
    g = client.get(f"/orders/{oid}")
    assert g.status_code == 200
    data = g.json()
    assert data["orderId"] == oid


