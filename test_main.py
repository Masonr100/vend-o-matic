import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def reset_machine():
    main.inventory[:] = [5, 5, 5]
    main.coins = 0


client = TestClient(main.app)


def insert_quarter():
    return client.put("/", json={"coin": 1})


def test_initial_inventory():
    response = client.get("/inventory")

    assert response.status_code == 200
    assert response.json() == [5, 5, 5]


def test_insert_and_cancel():
    insert_quarter()
    response = insert_quarter()

    assert response.status_code == 204
    assert response.headers["X-Coins"] == "2"

    response = client.delete("/")

    assert response.status_code == 204
    assert response.headers["X-Coins"] == "2"

    response = client.delete("/")
    assert response.headers["X-Coins"] == "0"


def test_purchase_with_change():
    for _ in range(3):
        insert_quarter()

    response = client.put("/inventory/0")

    assert response.status_code == 200
    assert response.json() == {"quantity": 1}
    assert response.headers["X-Coins"] == "1"
    assert response.headers["X-Inventory-Remaining"] == "4"
    assert client.get("/inventory").json() == [4, 5, 5]


def test_purchase_with_insufficient_coins():
    insert_quarter()

    response = client.put("/inventory/0")

    assert response.status_code == 403
    assert response.headers["X-Coins"] == "1"
    assert client.get("/inventory/0").json() == 5


def test_purchase_out_of_stock():
    # Buy all five drinks.
    for _ in range(5):
        insert_quarter()
        insert_quarter()

        response = client.put("/inventory/0")
        assert response.status_code == 200

    assert client.get("/inventory/0").json() == 0

    # Try to buy another drink after it sells out.
    insert_quarter()
    insert_quarter()

    response = client.put("/inventory/0")

    assert response.status_code == 404
    assert response.headers["X-Coins"] == "2"
    assert client.get("/inventory/0").json() == 0

    # The customer can still cancel and get their quarters back.
    cancel_response = client.delete("/")
    assert cancel_response.headers["X-Coins"] == "2"

def test_cannot_insert_multiple_coins_at_once():
    response = client.put("/", json={"coin": 2})

    assert response.status_code == 400

    # Cancelling should return zero because no coin was accepted.
    cancel_response = client.delete("/")
    assert cancel_response.headers["X-Coins"] == "0"

def test_purchase_with_exact_amount():
    insert_quarter()
    insert_quarter()

    response = client.put("/inventory/1")

    assert response.status_code == 200
    assert response.json() == {"quantity": 1}
    assert response.headers["X-Coins"] == "0"
    assert response.headers["X-Inventory-Remaining"] == "4"
    assert client.get("/inventory").json() == [5, 4, 5]

    # The purchase should reset the coin count.
    cancel_response = client.delete("/")
    assert cancel_response.headers["X-Coins"] == "0"

@pytest.mark.parametrize("invalid_coin", ["1", True])
def test_coin_must_be_an_integer(invalid_coin):
    response = client.put("/", json={"coin": invalid_coin})

    assert response.status_code == 422

    cancel_response = client.delete("/")
    assert cancel_response.headers["X-Coins"] == "0"

@pytest.mark.parametrize("item_id", [-1, 3])
def test_purchase_invalid_item(item_id):
    insert_quarter()
    insert_quarter()

    response = client.put(f"/inventory/{item_id}")

    assert response.status_code == 404
    assert response.headers["X-Coins"] == "2"
    assert client.get("/inventory").json() == [5, 5, 5]

    cancel_response = client.delete("/")
    assert cancel_response.headers["X-Coins"] == "2"