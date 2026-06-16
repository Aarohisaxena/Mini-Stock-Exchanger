import os
from typing import Callable, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base, OrderRecord, TradeRecord
from app.engine import MatchingEngine
from models.order import Order, OrderSide, OrderStatus, OrderType


class OrderService:
    def __init__(
        self,
        engine: Optional[MatchingEngine] = None,
        on_trade: Optional[Callable[[], None]] = None,
    ) -> None:
        self.engine = engine or MatchingEngine()
        self._on_trade = on_trade
        self._db_enabled = False
        self._SessionLocal: Optional[sessionmaker] = None

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self._init_db(database_url)

    def _init_db(self, database_url: str) -> None:
        db_engine = create_engine(database_url)
        Base.metadata.create_all(db_engine)
        self._SessionLocal = sessionmaker(bind=db_engine, autoflush=False)
        self._db_enabled = True

    def _persist_order(self, order: Order) -> None:
        if not self._db_enabled or self._SessionLocal is None:
            return
        with self._SessionLocal() as session:
            record = OrderRecord(
                id=order.order_id,
                user_id=order.user_id,
                side=order.side.value,
                order_type=order.order_type.value,
                price=order.price,
                quantity=order.quantity,
                remaining_quantity=order.remaining_quantity,
                status=order.status.value,
            )
            session.merge(record)
            session.commit()

    def _persist_trade(self, trade) -> None:
        if not self._db_enabled or self._SessionLocal is None:
            return
        with self._SessionLocal() as session:
            session.add(
                TradeRecord(
                    id=trade.trade_id,
                    buy_order_id=trade.buy_order_id,
                    sell_order_id=trade.sell_order_id,
                    price=trade.price,
                    quantity=trade.quantity,
                    timestamp=trade.timestamp,
                )
            )
            session.commit()

    def place_order(
        self,
        side: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: str = "limit",
        user_id: str = "default_user",
    ) -> dict:
        order = Order(
            user_id=user_id,
            side=OrderSide(side),
            quantity=quantity,
            order_type=OrderType(order_type),
            price=price,
        )
        order, trades = self.engine.submit_order(order)
        self._persist_order(order)

        for trade in trades:
            self._persist_trade(trade)
            if self._on_trade:
                self._on_trade()

        return {"order_id": order.order_id, "status": order.status.value}

    def get_orderbook(self) -> dict:
        return self.engine.get_orderbook()

    def get_trades(self, full: bool = False) -> List[dict]:
        trades = self.engine.get_trades()
        if full:
            return trades
        return [{"price": t["price"], "quantity": t["quantity"]} for t in trades]

    def cancel_order(self, order_id: str) -> Optional[dict]:
        order = self.engine.cancel_order(order_id)
        if order is None:
            return None
        self._persist_order(order)
        return {"order_id": order.order_id, "status": order.status.value}

    def modify_order(
        self, order_id: str, price: Optional[float] = None, quantity: Optional[int] = None
    ) -> Optional[dict]:
        order, trades = self.engine.modify_order(order_id, price=price, quantity=quantity)
        if order is None:
            return None
        self._persist_order(order)
        for trade in trades:
            self._persist_trade(trade)
            if self._on_trade:
                self._on_trade()
        return {"order_id": order.order_id, "status": order.status.value}
