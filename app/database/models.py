from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.database.connection import Base

__all__ = ["Base", "OrderRecord", "TradeRecord"]


class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(String, nullable=False, default="limit")
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TradeRecord(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True)
    buy_order_id = Column(String, nullable=False)
    sell_order_id = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
