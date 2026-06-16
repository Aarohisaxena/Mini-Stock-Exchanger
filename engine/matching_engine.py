from typing import List, Optional, Tuple

from engine.orderbook import OrderBook
from engine.trade import Trade, TradeStore
from models.order import Order, OrderSide, OrderStatus, OrderType


class MatchingEngine:
    """
    Central matching engine.

    Matching rule: highest bid >= lowest ask → trade at the resting order's price.
    Supports partial fills, market orders, cancellation, and modification.
    """

    def __init__(self) -> None:
        self.orderbook = OrderBook()
        self.trade_store = TradeStore()

    def submit_order(self, order: Order) -> Tuple[Order, List[Trade]]:
        trades: List[Trade] = []

        if order.side == OrderSide.BUY:
            trades = self._match_buy(order)
        else:
            trades = self._match_sell(order)

        # Resting limit orders with remaining quantity go on the book
        if (
            not order.is_filled
            and order.status != OrderStatus.CANCELLED
            and order.order_type == OrderType.LIMIT
        ):
            self.orderbook.add_order(order)

        return order, trades

    def cancel_order(self, order_id: str) -> Optional[Order]:
        order = self.orderbook.remove_order(order_id)
        return order

    def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None,
    ) -> Tuple[Optional[Order], List[Trade]]:
        existing = self.orderbook.get_order(order_id)
        if existing is None or existing.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
        ):
            return None, []

        new_order = Order(
            order_id=existing.order_id,
            user_id=existing.user_id,
            side=existing.side,
            order_type=existing.order_type,
            price=price if price is not None else existing.price,
            quantity=quantity if quantity is not None else existing.remaining_quantity,
            timestamp=existing.timestamp,
        )
        self.orderbook.remove_order(order_id)
        return self.submit_order(new_order)

    def _match_buy(self, order: Order) -> List[Trade]:
        trades: List[Trade] = []
        while not order.is_filled and self.orderbook.can_match(order):
            ask = self.orderbook.best_ask()
            if ask is None:
                break
            if not order.is_market and order.price < ask.price:
                break
            trade = self._execute_trade(order, ask, trade_price=ask.price)
            trades.append(trade)
            self.trade_store.add(trade)
        if order.is_market and not order.is_filled:
            order.cancel()
        return trades

    def _match_sell(self, order: Order) -> List[Trade]:
        trades: List[Trade] = []
        while not order.is_filled and self.orderbook.can_match(order):
            bid = self.orderbook.best_bid()
            if bid is None:
                break
            if not order.is_market and order.price > bid.price:
                break
            trade = self._execute_trade(bid, order, trade_price=bid.price)
            trades.append(trade)
            self.trade_store.add(trade)
        if order.is_market and not order.is_filled:
            order.cancel()
        return trades

    def _execute_trade(
        self, buy_order: Order, sell_order: Order, trade_price: float
    ) -> Trade:
        quantity = min(buy_order.remaining_quantity, sell_order.remaining_quantity)

        buy_order.fill(quantity)
        sell_order.fill(quantity)

        if buy_order.is_filled:
            self.orderbook._orders.pop(buy_order.order_id, None)
        if sell_order.is_filled:
            self.orderbook._orders.pop(sell_order.order_id, None)

        return Trade(
            buyer=buy_order.user_id,
            seller=sell_order.user_id,
            price=trade_price,
            quantity=quantity,
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
        )

    def get_orderbook(self) -> dict:
        return self.orderbook.get_orderbook_snapshot()

    def get_trades(self) -> List[dict]:
        return [t.to_dict() for t in self.trade_store.get_all()]
