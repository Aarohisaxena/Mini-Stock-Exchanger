import asyncio
import json
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import orders, trades
from app.services.order_service import OrderService


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        dead: Set[WebSocket] = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.add(connection)
        for connection in dead:
            self.disconnect(connection)


def create_app() -> FastAPI:
    manager = ConnectionManager()
    pending_broadcasts: list = []
    order_service = OrderService()
    runtime_state: dict = {"loop": None}

    async def broadcast_orderbook() -> None:
        book = order_service.get_orderbook()
        await manager.broadcast({"type": "orderbook", "data": book})

    def on_trade() -> None:
        loop = runtime_state.get("loop")
        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_orderbook(), loop)
        else:
            pending_broadcasts.append(True)

    order_service._on_trade = on_trade

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime_state["loop"] = asyncio.get_running_loop()
        app.state.loop = runtime_state["loop"]
        while pending_broadcasts:
            pending_broadcasts.pop()
            await broadcast_orderbook()
        yield

    app = FastAPI(
        title="Mini Stock Exchange",
        description="Order matching engine with live order book WebSocket feed",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.connection_manager = manager
    app.state.order_service = order_service

    app.include_router(orders.router)
    app.include_router(trades.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.websocket("/ws/orderbook")
    async def websocket_orderbook(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            book = app.state.order_service.get_orderbook()
            await websocket.send_json({"type": "orderbook", "data": book})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app


app = create_app()
