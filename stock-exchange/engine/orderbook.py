import heapq
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from models.order import Order, OrderSide, OrderStatus


class OrderBook:
    """
    Price-time priority order book using heaps.

    Buy side: max-heap (negated price) — highest price wins.
    Sell side: min-heap — lowest price wins.
    """

    def __init__(self) -> None:
        self._buy_heap: List[Tuple] = []
        self._sell_heap: List[Tuple] = []
        self._orders: Dict[str, Order] = {}

    def add_order(self, order: Order) -> None:
        self._orders[order.order_id] = order
        if order.side == OrderSide.BUY:
            heapq.heappush(self._buy_heap, (self._buy_key(order), order.order_id))
        else:
            heapq.heappush(self._sell_heap, (self._sell_key(order), order.order_id))

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def remove_order(self, order_id: str) -> Optional[Order]:
        order = self._orders.pop(order_id, None)
        if order is not None:
            order.cancel()
        return order

    def _buy_key(self, order: Order) -> Tuple:
        # Max-heap via negated price; earlier timestamp wins at same price
        return (-order.price, order.timestamp, order.order_id)

    def _sell_key(self, order: Order) -> Tuple:
        return (order.price, order.timestamp, order.order_id)

    def _peek_valid(self, heap: List[Tuple], side: OrderSide) -> Optional[Order]:
        while heap:
            _, order_id = heap[0]
            order = self._orders.get(order_id)
            if order is None or order.status == OrderStatus.CANCELLED or order.is_filled:
                heapq.heappop(heap)
                continue
            if order.side != side:
                heapq.heappop(heap)
                continue
            return order
        return None

    def best_bid(self) -> Optional[Order]:
        return self._peek_valid(self._buy_heap, OrderSide.BUY)

    def best_ask(self) -> Optional[Order]:
        return self._peek_valid(self._sell_heap, OrderSide.SELL)

    def can_match(self, incoming: Order) -> bool:
        if incoming.is_market:
            if incoming.side == OrderSide.BUY:
                return self.best_ask() is not None
            return self.best_bid() is not None

        if incoming.side == OrderSide.BUY:
            ask = self.best_ask()
            return ask is not None and incoming.price >= ask.price
        bid = self.best_bid()
        return bid is not None and incoming.price <= bid.price

    def get_orderbook_snapshot(self) -> dict:
        """Aggregate open orders by price level for API response."""
        bids: Dict[float, int] = defaultdict(int)
        asks: Dict[float, int] = defaultdict(int)

        for order in self._orders.values():
            if order.status in (OrderStatus.CANCELLED, OrderStatus.FILLED):
                continue
            if order.is_market:
                continue
            if order.side == OrderSide.BUY:
                bids[order.price] += order.remaining_quantity
            else:
                asks[order.price] += order.remaining_quantity

        bid_levels = sorted(
            [{"price": price, "qty": qty} for price, qty in bids.items()],
            key=lambda x: x["price"],
            reverse=True,
        )
        ask_levels = sorted(
            [{"price": price, "qty": qty} for price, qty in asks.items()],
            key=lambda x: x["price"],
        )
        return {"bids": bid_levels, "asks": ask_levels}
