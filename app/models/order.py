from pydantic import BaseModel, Field
from typing import Literal, Optional


class PlaceOrderRequest(BaseModel):
    side: Literal["buy", "sell"]
    quantity: int = Field(gt=0)
    type: Literal["limit", "market"] = "limit"
    price: Optional[float] = Field(default=None, gt=0)
    user_id: str = "default_user"


class PlaceOrderResponse(BaseModel):
    order_id: str
    status: str


class OrderBookLevel(BaseModel):
    price: float
    qty: int


class OrderBookResponse(BaseModel):
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]


class TradeResponse(BaseModel):
    price: float
    quantity: int
    trade_id: Optional[str] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    timestamp: Optional[float] = None


class ModifyOrderRequest(BaseModel):
    price: Optional[float] = Field(default=None, gt=0)
    quantity: Optional[int] = Field(default=None, gt=0)
