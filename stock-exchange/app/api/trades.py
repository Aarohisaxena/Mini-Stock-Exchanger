from fastapi import APIRouter, Request

from app.models.order import OrderBookResponse, TradeResponse

router = APIRouter(tags=["market-data"])


@router.get("/orderbook", response_model=OrderBookResponse)
def get_orderbook(request: Request):
    service = request.app.state.order_service
    book = service.get_orderbook()
    return OrderBookResponse(**book)


@router.get("/trades", response_model=list[TradeResponse])
def get_trades(request: Request, full: bool = False):
    service = request.app.state.order_service
    return service.get_trades(full=full)
