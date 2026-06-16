from fastapi import APIRouter, HTTPException, Request

from app.models.order import ModifyOrderRequest, PlaceOrderRequest, PlaceOrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=PlaceOrderResponse)
def place_order(request_body: PlaceOrderRequest, request: Request):
    service = request.app.state.order_service

    if request_body.type == "limit" and request_body.price is None:
        raise HTTPException(status_code=400, detail="Limit orders require a price")

    try:
        result = service.place_order(
            side=request_body.side,
            quantity=request_body.quantity,
            price=request_body.price,
            order_type=request_body.type,
            user_id=request_body.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlaceOrderResponse(**result)


@router.delete("/{order_id}")
def cancel_order(order_id: str, request: Request):
    service = request.app.state.order_service
    result = service.cancel_order(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.patch("/{order_id}")
def modify_order(order_id: str, body: ModifyOrderRequest, request: Request):
    service = request.app.state.order_service
    if body.price is None and body.quantity is None:
        raise HTTPException(status_code=400, detail="Provide price or quantity to modify")

    result = service.modify_order(order_id, price=body.price, quantity=body.quantity)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found or not modifiable")
    return result
