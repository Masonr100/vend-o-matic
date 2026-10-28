# Vend-O-Matic

A Python API that simulates a beverage vending machine. It accepts quarters,
tracks inventory, dispenses drinks, and returns change.

## Requirements

- Python 3.12
- pip

## Setup

Clone the repository and enter the project folder:

```bash
git clone https://github.com/Masonr100/vend-o-matic.git
cd vend-o-matic
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the application

```bash
uvicorn main:app --workers 1
```

The API runs at `http://127.0.0.1:8000`. You can use the interactive
documentation at `http://127.0.0.1:8000/docs`.

## Run the tests

```bash
python -m pytest -v
```

## How it works

- The machine starts with three drinks, with five of each in stock.
- Drink IDs are `0`, `1`, and `2`.
- Each drink costs two quarters.
- Each `PUT /` request accepts one quarter using `{"coin": 1}`.
- A successful purchase dispenses one drink and returns any extra quarters.
- Canceling returns all quarters inserted for the current transaction.
- Inventory and coins are stored in memory and reset when the server restarts.
- Run one worker so requests share the same in-memory machine state.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `PUT` | `/` | Insert one quarter |
| `DELETE` | `/` | Cancel and return inserted quarters |
| `GET` | `/inventory` | Get the quantity of all three drinks |
| `GET` | `/inventory/{item_id}` | Get one drink's quantity |
| `PUT` | `/inventory/{item_id}` | Purchase one drink |

The `X-Coins` header reports the number of quarters accepted or returned,
depending on the endpoint. A successful purchase also returns
`X-Inventory-Remaining`.

## Example transaction

Insert two quarters by running this command twice:

```bash
curl -i -X PUT http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{"coin": 1}'
```

Then purchase drink `0`:

```bash
curl -i -X PUT http://127.0.0.1:8000/inventory/0 \
  -H "Content-Type: application/json"
```

On a freshly started machine, the response body should be `{"quantity": 1}`.
The headers should include `X-Coins: 0` and `X-Inventory-Remaining: 4`.

If fewer than two quarters have been inserted, a purchase returns `403` and
the `X-Coins` header shows how many quarters are currently held. An
out-of-stock drink returns `404` and also reports the current coin count.

## Design decisions

- **FastAPI:** Provides HTTP routing, JSON handling, input validation,
  and interactive API documentation.
- **Integer coin counts:** All monetary values are tracked as counts of
  quarters, avoiding floating-point arithmetic.
- **In-memory state:** Keeps the service small and avoids a database
  dependency. Inventory and inserted coins reset when the server restarts.
- **Thread lock:** Protects inventory and coin operations from conflicting
  updates within a single server process. The application must run with
  one worker because separate processes do not share this state.
- **Failed purchases preserve state:** Customers can add another quarter,
  choose another beverage, or cancel without losing inserted coins.
- **Item IDs:** The specification does not define the ID range, so this
  implementation uses IDs 0, 1, and 2.
- **Out-of-stock precedence:** Stock is checked before funds, so a sold-out
  beverage returns 404 even when fewer than two quarters are inserted.

## Verification

The test suite covers inventory, coin insertion, cancellation, purchases,
change, invalid inputs, sold-out beverages, and concurrent purchase
attempts for the last beverage.

GitHub Actions installs dependencies and runs the tests on macOS for
pushes and pull requests.

## Production considerations

This service models one vending machine with one shared transaction.
It assumes the physical machine accepts only quarters, as specified.

A production implementation would need a trusted connection to the
machine's hardware, durable state, and a strategy for recovering from
failures between recording a purchase and physically dispensing a drink.
