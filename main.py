from fastapi import FastAPI, Response
from pydantic import BaseModel, StrictInt
from threading import Lock

app = FastAPI()

inventory = [5, 5, 5]
coins = 0
machine_lock = Lock()


@app.get("/inventory")
def get_inventory():
    with machine_lock:
        return inventory.copy()

class CoinRequest(BaseModel):
    coin: StrictInt


@app.put("/", status_code=204)
def insert_coin(request: CoinRequest, response: Response):
    global coins

    if request.coin != 1:
        response.status_code = 400
        return

    with machine_lock:
        coins += 1
        response.headers["X-Coins"] = str(coins)

@app.delete("/", status_code=204)
def cancel_transaction(response: Response):
    global coins

    with machine_lock:
        returned_coins = coins
        coins = 0

    response.headers["X-Coins"] = str(returned_coins)

@app.get("/inventory/{item_id}")
def get_item_inventory(item_id: int, response: Response):
    with machine_lock:
        if item_id < 0 or item_id >= len(inventory):
            response.status_code = 404
            return {"detail": "Item not found"}

        return inventory[item_id]

@app.put("/inventory/{item_id}")
def purchase_item(item_id: int, response: Response):
    global coins

    with machine_lock:
        if item_id < 0 or item_id >= len(inventory):
            response.status_code = 404
            response.headers["X-Coins"] = str(coins)
            return {"detail": "Item not found"}

        if inventory[item_id] == 0:
            response.status_code = 404
            response.headers["X-Coins"] = str(coins)
            return {"detail": "Item is out of stock"}

        if coins < 2:
            response.status_code = 403
            response.headers["X-Coins"] = str(coins)
            return {"detail": "Not enough coins"}

        inventory[item_id] -= 1
        change = coins - 2
        coins = 0

        response.headers["X-Coins"] = str(change)
        response.headers["X-Inventory-Remaining"] = str(inventory[item_id])

        return {"quantity": 1}