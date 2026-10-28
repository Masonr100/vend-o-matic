from fastapi import FastAPI, Response
from pydantic import BaseModel, StrictInt
from threading import Lock
from fastapi.responses import JSONResponse

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

class PurchaseResponse(BaseModel):
    quantity: StrictInt


@app.put(
    "/inventory/{item_id}",
    response_model=PurchaseResponse,
    summary="Purchase one beverage",
    responses={
        200: {
            "description": "One beverage dispensed; extra quarters returned.",
        },
        403: {
            "description": (
                "Fewer than two quarters inserted. "
                "Coins remain available for purchase or cancellation."
            ),
        },
        404: {
            "description": (
                "The beverage does not exist or is out of stock. "
                "Inventory and inserted coins are unchanged."
            ),
        },
    },
)
def purchase_item(item_id: int, response: Response):
    global coins

    with machine_lock:
        if item_id < 0 or item_id >= len(inventory):
            return JSONResponse(
                status_code=404,
                headers={"X-Coins": str(coins)},
                content={"detail": "Item not found"},
            )

        if inventory[item_id] == 0:
            return JSONResponse(
                status_code=404,
                headers={"X-Coins": str(coins)},
                content={"detail": "Item is out of stock"},
            )

        if coins < 2:
            return JSONResponse(
                status_code=403,
                headers={"X-Coins": str(coins)},
                content={"detail": "Not enough coins"},
            )

        inventory[item_id] -= 1
        change = coins - 2
        coins = 0

        response.headers["X-Coins"] = str(change)
        response.headers["X-Inventory-Remaining"] = str(inventory[item_id])

        return {"quantity": 1}