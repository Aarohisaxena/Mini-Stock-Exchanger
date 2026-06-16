"""API integration tests."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_place_order_and_orderbook(client):
    response = client.post(
        "/orders",
        json={"side": "buy", "price": 100, "quantity": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["status"] == "open"

    book = client.get("/orderbook").json()
    assert book["bids"] == [{"price": 100, "qty": 10}]


def test_matching_via_api(client):
    client.post("/orders", json={"side": "sell", "price": 100, "quantity": 5})
    client.post("/orders", json={"side": "buy", "price": 105, "quantity": 5})

    trades = client.get("/trades").json()
    assert len(trades) == 1
    assert trades[0]["price"] == 100
    assert trades[0]["quantity"] == 5


def test_partial_fill_via_api(client):
    client.post("/orders", json={"side": "sell", "price": 104, "quantity": 40})
    client.post("/orders", json={"side": "buy", "price": 105, "quantity": 100})

    trades = client.get("/trades").json()
    assert trades[0]["quantity"] == 40

    book = client.get("/orderbook").json()
    assert book["bids"] == [{"price": 105, "qty": 60}]


def test_market_order_via_api(client):
    client.post("/orders", json={"side": "sell", "price": 100, "quantity": 5})
    response = client.post(
        "/orders",
        json={"side": "buy", "quantity": 10, "type": "market"},
    )
    assert response.json()["status"] == "cancelled"


def test_cancel_order(client):
    placed = client.post(
        "/orders",
        json={"side": "buy", "price": 100, "quantity": 10},
    ).json()
    response = client.delete(f"/orders/{placed['order_id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get("/orderbook").json()["bids"] == []


def test_modify_order(client):
    placed = client.post(
        "/orders",
        json={"side": "buy", "price": 100, "quantity": 10},
    ).json()
    response = client.patch(
        f"/orders/{placed['order_id']}",
        json={"price": 110, "quantity": 5},
    )
    assert response.status_code == 200
    book = client.get("/orderbook").json()
    assert book["bids"] == [{"price": 110, "qty": 5}]
