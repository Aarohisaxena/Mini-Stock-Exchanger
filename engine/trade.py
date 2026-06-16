from dataclasses import dataclass, field
from typing import List
import time
import uuid


@dataclass
class Trade:
    buyer: str
    seller: str
    price: float
    quantity: int
    buy_order_id: str
    sell_order_id: str
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "buyer": self.buyer,
            "seller": self.seller,
            "price": self.price,
            "quantity": self.quantity,
            "buy_order_id": self.buy_order_id,
            "sell_order_id": self.sell_order_id,
            "timestamp": self.timestamp,
        }


class TradeStore:
    """In-memory store for executed trades."""

    def __init__(self) -> None:
        self._trades: List[Trade] = []

    def add(self, trade: Trade) -> None:
        self._trades.append(trade)

    def get_all(self) -> List[Trade]:
        return list(self._trades)

    def clear(self) -> None:
        self._trades.clear()
