# Vend-O-Matic

A Python API that simulates a beverage vending machine. It accepts quarters,
tracks inventory, dispenses drinks, and returns change.

## Requirements

- Python 3.12
- pip

## Setup

Clone the repository and enter the project folder:

```bash
git clone <repository-url>
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
