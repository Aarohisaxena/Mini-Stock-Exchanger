from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    user_id: str
    side: OrderSide
    quantity: int
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_type: OrderType = OrderType.LIMIT
    price: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    remaining_quantity: Optional[int] = None
    status: OrderStatus = OrderStatus.OPEN

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("limit orders require a price")
        if self.order_type == OrderType.LIMIT and self.price <= 0:
            raise ValueError("price must be positive")
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity

    @property
    def is_filled(self) -> bool:
        return self.remaining_quantity == 0

    @property
    def is_market(self) -> bool:
        return self.order_type == OrderType.MARKET

    def fill(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")
        if quantity > self.remaining_quantity:
            raise ValueError("fill quantity exceeds remaining quantity")
        self.remaining_quantity -= quantity
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "side": self.side.value,
            "type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "remaining_quantity": self.remaining_quantity,
            "timestamp": self.timestamp,
            "status": self.status.value,
        }
