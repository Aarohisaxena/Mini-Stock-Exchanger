"""Phase 1 tests for the core matching engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.matching_engine import MatchingEngine
from models.order import Order, OrderSide, OrderStatus, OrderType


def test_basic_match():
    engine = MatchingEngine()

    sell = Order(user_id="seller", side=OrderSide.SELL, price=100, quantity=10)
    buy = Order(user_id="buyer", side=OrderSide.BUY, price=105, quantity=10)

    _, trades = engine.submit_order(sell)
    assert len(trades) == 0

    order, trades = engine.submit_order(buy)
    assert len(trades) == 1
    assert trades[0].price == 100
    assert trades[0].quantity == 10
    assert order.status == OrderStatus.FILLED


def test_partial_fill():
    engine = MatchingEngine()

    sell = Order(user_id="seller", side=OrderSide.SELL, price=104, quantity=40)
    buy = Order(user_id="buyer", side=OrderSide.BUY, price=105, quantity=100)

    engine.submit_order(sell)
    order, trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == 40
    assert order.remaining_quantity == 60
    assert order.status == OrderStatus.PARTIALLY_FILLED

    book = engine.get_orderbook()
    assert book["bids"] == [{"price": 105, "qty": 60}]


def test_order_book_priority():
    engine = MatchingEngine()

    engine.submit_order(Order(user_id="A", side=OrderSide.BUY, price=103, quantity=5))
    engine.submit_order(Order(user_id="B", side=OrderSide.BUY, price=105, quantity=10))
    engine.submit_order(Order(user_id="C", side=OrderSide.SELL, price=110, quantity=5))
    engine.submit_order(Order(user_id="D", side=OrderSide.SELL, price=108, quantity=3))

    book = engine.get_orderbook()
    assert book["bids"][0] == {"price": 105, "qty": 10}
    assert book["bids"][1] == {"price": 103, "qty": 5}
    assert book["asks"][0] == {"price": 108, "qty": 3}
    assert book["asks"][1] == {"price": 110, "qty": 5}


def test_no_match_when_spread():
    engine = MatchingEngine()

    engine.submit_order(Order(user_id="A", side=OrderSide.BUY, price=100, quantity=10))
    engine.submit_order(Order(user_id="B", side=OrderSide.SELL, price=105, quantity=10))

    book = engine.get_orderbook()
    assert len(book["bids"]) == 1
    assert len(book["asks"]) == 1
    assert len(engine.get_trades()) == 0


def test_market_order():
    engine = MatchingEngine()

    engine.submit_order(Order(user_id="S", side=OrderSide.SELL, price=100, quantity=5))
    buy = Order(
        user_id="B", side=OrderSide.BUY, quantity=10, order_type=OrderType.MARKET
    )
    order, trades = engine.submit_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == 5
    assert trades[0].price == 100
    assert order.status == OrderStatus.CANCELLED


def test_cancel_order():
    engine = MatchingEngine()

    order = Order(user_id="A", side=OrderSide.BUY, price=100, quantity=10)
    engine.submit_order(order)
    cancelled = engine.cancel_order(order.order_id)

    assert cancelled is not None
    assert cancelled.status == OrderStatus.CANCELLED
    assert engine.get_orderbook()["bids"] == []


def test_modify_order():
    engine = MatchingEngine()

    order = Order(user_id="A", side=OrderSide.BUY, price=100, quantity=10)
    engine.submit_order(order)
    updated, trades = engine.modify_order(order.order_id, price=110, quantity=5)

    assert updated is not None
    assert updated.price == 110
    assert updated.quantity == 5
    book = engine.get_orderbook()
    assert book["bids"] == [{"price": 110, "qty": 5}]


if __name__ == "__main__":
    test_basic_match()
    test_partial_fill()
    test_order_book_priority()
    test_no_match_when_spread()
    test_market_order()
    test_cancel_order()
    test_modify_order()
    print("All Phase 1 tests passed!")
